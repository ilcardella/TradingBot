import json
import logging
from enum import Enum
from typing import Any, Dict, List, Optional

import pandas
import requests

from ...interfaces import Market, MarketHistory, MarketMACD, Position
from .. import Interval, TradeDirection, Utils
from . import AccountBalances, AccountInterface, StocksInterface


class IG_API_URL(Enum):
    """
    IG REST API urls
    """

    BASE_URI = "https://@api.ig.com/gateway/deal"
    DEMO_PREFIX = "demo-"
    SESSION = "session"
    ACCOUNTS = "accounts"
    POSITIONS = "positions"
    POSITIONS_OTC = "positions/otc"
    MARKETS = "markets"
    PRICES = "prices"
    CONFIRMS = "confirms"
    MARKET_NAV = "marketnavigation"
    WATCHLISTS = "watchlists"


class IGInterface(AccountInterface, StocksInterface):
    """
    IG broker interface class, provides functions to use the IG REST API
    """

    api_base_url: str
    authenticated_headers: Dict[str, str]

    def initialise(self) -> None:
        logging.info("initialising IGInterface...")
        demoPrefix = (
            IG_API_URL.DEMO_PREFIX.value
            if self._config.get_ig_use_demo_account()
            else ""
        )
        self.api_base_url = IG_API_URL.BASE_URI.value.replace("@", demoPrefix)
        self.authenticated_headers = {}
        if self._config.is_paper_trading_enabled():
            logging.info("Paper trading is active")
        if not self.authenticate():
            logging.error("Authentication failed")
            raise RuntimeError("Unable to authenticate to IG Index. Check credentials")

    def authenticate(self) -> bool:
        """
        Authenticate the IGInterface instance with the configured credentials
        """
        data = {
            "identifier": self._config.get_credentials()["username"],
            "password": self._config.get_credentials()["password"],
        }
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json; charset=utf-8",
            "X-IG-API-KEY": self._config.get_credentials()["api_key"],
            "Version": "2",
        }
        url = "{}/{}".format(self.api_base_url, IG_API_URL.SESSION.value)
        response = requests.post(url, data=json.dumps(data), headers=headers)

        if response.status_code != 200:
            logging.debug(
                "Authentication returned code: {}".format(response.status_code)
            )
            return False

        headers_json = dict(response.headers)
        try:
            CST_token = headers_json["CST"]
            x_sec_token = headers_json["X-SECURITY-TOKEN"]
        except Exception:
            return False

        self.authenticated_headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json; charset=utf-8",
            "X-IG-API-KEY": self._config.get_credentials()["api_key"],
            "CST": CST_token,
            "X-SECURITY-TOKEN": x_sec_token,
        }

        self.set_default_account(self._config.get_credentials()["account_id"])
        return True

    def set_default_account(self, accountId: str) -> bool:
        """
        Sets the IG account to use

            - **accountId**: String representing the accound id to use
            - Returns **False** if an error occurs otherwise True
        """
        url = "{}/{}".format(self.api_base_url, IG_API_URL.SESSION.value)
        data = {"accountId": accountId, "defaultAccount": "True"}
        response = requests.put(
            url, data=json.dumps(data), headers=self.authenticated_headers
        )

        if response.status_code != 200:
            return False

        logging.info("Default IG account set")
        return True

    def get_account_balances(self) -> AccountBalances:
        """
        Returns a tuple (balance, deposit) for the account in use

            - Returns **(None,None)** if an error occurs otherwise (balance, deposit)
        """
        url = "{}/{}".format(self.api_base_url, IG_API_URL.ACCOUNTS.value)
        d = self._http_get(url)
        if d is not None:
            try:
                for i in d["accounts"]:
                    if str(i["accountType"]) == "SPREADBET":
                        balance = i["balance"]["balance"]
                        deposit = i["balance"]["deposit"]
                        return balance, deposit
            except Exception:
                return None, None
        return None, None

    def get_open_positions(self) -> List[Position]:
        """
        Returns the account open positions in an json object

            - Returns the json object returned by the IG API
        """
        url = "{}/{}".format(self.api_base_url, IG_API_URL.POSITIONS.value)
        data = self._http_get(url)
        positions = []
        for d in data["positions"]:
            positions.append(
                Position(
                    deal_id=d["position"]["dealId"],
                    size=d["position"]["size"],
                    create_date=d["position"]["createdDateUTC"],
                    direction=TradeDirection[d["position"]["direction"]],
                    level=d["position"]["level"],
                    limit=d["position"]["limitLevel"],
                    stop=d["position"]["stopLevel"],
                    currency=d["position"]["currency"],
                    epic=d["market"]["epic"],
                    market_id=None,
                )
            )
        return positions

    def get_positions_map(self) -> Dict[str, int]:
        """
        Returns a *dict* containing the account open positions in the form
        {string: int} where the string is defined as 'marketId-tradeDirection' and
        the int is the trade size

            - Returns **None** if an error occurs otherwise a dict(string:int)
        """
        positionMap: Dict[str, int] = {}
        for item in self.get_open_positions():
            key = item.epic + "-" + item.direction.name
            if key in positionMap:
                positionMap[key] = item.size + positionMap[key]
            else:
                positionMap[key] = item.size
        return positionMap

    def get_market_info(self, epic_id: str) -> Market:
        """
        Returns info for the given market including a price snapshot

            - **epic_id**: market epic as string
            - Returns **None** if an error occurs otherwise the json returned by IG API
        """
        url = "{}/{}/{}".format(self.api_base_url, IG_API_URL.MARKETS.value, epic_id)
        info = self._http_get(url)

        if "markets" in info:
            raise RuntimeError("Multiple matches found for epic: {}".format(epic_id))
        if self._config.get_ig_controlled_risk():
            info["minNormalStopOrLimitDistance"] = info["minControlledRiskStopDistance"]
        market = Market()
        market.epic = info["instrument"]["epic"]
        market.id = info["instrument"]["marketId"]
        market.name = info["instrument"]["name"]
        market.bid = info["snapshot"]["bid"]
        market.offer = info["snapshot"]["offer"]
        market.high = info["snapshot"]["high"]
        market.low = info["snapshot"]["low"]
        market.stop_distance_min = info["dealingRules"]["minNormalStopOrLimitDistance"][
            "value"
        ]
        market.expiry = info["instrument"]["expiry"]
        return market

    def search_market(self, search: str) -> List[Market]:
        """
        Returns a list of markets that matched the search string
        """
        url = "{}/{}?searchTerm={}".format(
            self.api_base_url, IG_API_URL.MARKETS.value, search
        )
        data = self._http_get(url)
        markets = []
        if data is not None and "markets" in data:
            markets = [self.get_market_info(m["epic"]) for m in data["markets"]]
        return markets

    def get_prices(
        self, market: Market, interval: Interval, data_range: int
    ) -> MarketHistory:
        url = "{}/{}/{}/{}/{}".format(
            self.api_base_url,
            IG_API_URL.PRICES.value,
            market.epic,
            interval,
            data_range,
        )
        data = self._http_get(url)
        if "allowance" in data:
            remaining_allowance = data["allowance"]["remainingAllowance"]
            reset_time = Utils.humanize_time(int(data["allowance"]["allowanceExpiry"]))
            if remaining_allowance < 100:
                logging.warn(
                    "Remaining API calls left: {}".format(str(remaining_allowance))
                )
                logging.warn("Time to API Key reset: {}".format(str(reset_time)))
        dates = []
        highs = []
        lows = []
        closes = []
        volumes = []
        for price in data["prices"]:
            dates.append(price["snapshotTimeUTC"])
            highs.append(price["highPrice"]["bid"])
            lows.append(price["lowPrice"]["bid"])
            closes.append(price["closePrice"]["bid"])
            volumes.append(float(price["lastTradedVolume"]))
        history = MarketHistory(market, dates, highs, lows, closes, volumes)
        return history

    def trade(
        self, epic_id: str, trade_direction: TradeDirection, limit: float, stop: float
    ) -> bool:
        """
        Try to open a new trade for the given epic

            - **epic_id**: market epic as string
            - **trade_direction**: BUY or SELL
            - **limit**: limit level
            - **stop**: stop level
            - Returns **False** if an error occurs otherwise True
        """
        if self._config.is_paper_trading_enabled():
            logging.info(
                "Paper trade: {} {} with limit={} and stop={}".format(
                    trade_direction.value, epic_id, limit, stop
                )
            )
            return True

        url = "{}/{}".format(self.api_base_url, IG_API_URL.POSITIONS_OTC.value)
        data = {
            "direction": trade_direction.value,
            "epic": epic_id,
            "limitLevel": limit,
            "orderType": self._config.get_ig_order_type(),
            "size": self._config.get_ig_order_size(),
            "expiry": self._config.get_ig_order_expiry(),
            "guaranteedStop": self._config.get_ig_use_g_stop(),
            "currencyCode": self._config.get_ig_order_currency(),
            "forceOpen": self._config.get_ig_order_force_open(),
            "stopLevel": stop,
        }

        r = requests.post(
            url, data=json.dumps(data), headers=self.authenticated_headers
        )

        if r.status_code != 200:
            return False

        d = json.loads(r.text)
        deal_ref = d["dealReference"]
        if self.confirm_order(deal_ref):
            logging.info(
                "Order {} for {} confirmed with limit={} and stop={}".format(
                    trade_direction.value, epic_id, limit, stop
                )
            )
            return True
        else:
            logging.warning(
                "Trade {} of {} has failed!".format(trade_direction.value, epic_id)
            )
            return False

    def confirm_order(self, dealRef: str) -> bool:
        """
        Confirm an order from a dealing reference

            - **dealRef**: dealing reference to confirm
            - Returns **False** if an error occurs otherwise True
        """
        url = "{}/{}/{}".format(self.api_base_url, IG_API_URL.CONFIRMS.value, dealRef)
        d = self._http_get(url)

        if d is not None:
            if d["reason"] != "SUCCESS":
                return False
            else:
                return True
        return False

    def close_position(self, position: Position) -> bool:
        """
        Close the given market position

            - **position**: position json object obtained from IG API
            - Returns **False** if an error occurs otherwise True
        """
        if self._config.is_paper_trading_enabled():
            logging.info("Paper trade: close {} position".format(position.epic))
            return True
        # To close we need the opposite direction
        direction = TradeDirection.NONE
        if position.direction is TradeDirection.BUY:
            direction = TradeDirection.SELL
        elif position.direction is TradeDirection.SELL:
            direction = TradeDirection.BUY
        else:
            logging.error("Wrong position direction!")
            return False

        url = "{}/{}".format(self.api_base_url, IG_API_URL.POSITIONS_OTC.value)
        data = {
            "dealId": position.deal_id,
            "epic": None,
            "expiry": None,
            "direction": direction.name,
            "size": "1",
            "level": None,
            "orderType": "MARKET",
            "timeInForce": None,
            "quoteId": None,
        }
        del_headers = dict(self.authenticated_headers)
        del_headers["_method"] = "DELETE"
        r = requests.post(url, data=json.dumps(data), headers=del_headers)
        if r.status_code != 200:
            return False
        d = json.loads(r.text)
        deal_ref = d["dealReference"]
        if self.confirm_order(deal_ref):
            logging.info("Position  for {} closed".format(position.epic))
            return True
        else:
            logging.error("Could not close position for {}".format(position.epic))
            return False

    def close_all_positions(self) -> bool:
        """
        Try to close all the account open positions.

            - Returns **False** if an error occurs otherwise True
        """
        result = True
        try:
            positions = self.get_open_positions()
            if positions is not None:
                for p in positions:
                    try:
                        if not self.close_position(p):
                            result = False
                    except Exception:
                        logging.error(
                            "Error closing position for {}".format(p.market_id)
                        )
                        result = False
            else:
                logging.error("Unable to retrieve open positions!")
                result = False
        except Exception:
            logging.error("Error during close all positions")
            result = False
        return result

    def get_account_used_perc(self) -> Optional[float]:
        """
        Fetch the percentage of available balance is currently used

            - Returns the percentage of account used over total available amount
        """
        balance, deposit = self.get_account_balances()
        if balance is None or deposit is None:
            return None
        return Utils.percentage(deposit, balance)

    def navigate_market_node(self, node_id: str) -> Dict[str, Any]:
        """
        Navigate the market node id

            - Returns the json representing the market node
        """
        url = "{}/{}/{}".format(self.api_base_url, IG_API_URL.MARKET_NAV.value, node_id)
        return self._http_get(url)

    def _get_watchlist(self, id: str) -> Dict[str, Any]:
        """
        Get the watchlist info

            - **id**: id of the watchlist. If empty id is provided, the
              function returns the list of all the watchlist in the account
        """
        url = "{}/{}/{}".format(self.api_base_url, IG_API_URL.WATCHLISTS.value, id)
        return self._http_get(url)

    def get_markets_from_watchlist(self, name: str) -> List[Market]:
        """
        Get the list of markets included in the watchlist

            - **name**: name of the watchlist
        """
        markets = []
        # Request with empty name returns list of all the watchlists
        all_watchlists = self._get_watchlist("")
        for w in all_watchlists["watchlists"]:
            if "name" in w and w["name"] == name:
                data = self._get_watchlist(w["id"])
                if "markets" in data:
                    for m in data["markets"]:
                        markets.append(self.get_market_info(m["epic"]))
                break
        return markets

    def _http_get(self, url: str) -> Dict[str, Any]:
        """
        Perform an HTTP GET request to the url.
        Return the json object returned from the API if 200 is received
        Return None if an error is received from the API
        """
        self._wait_before_call(self._config.get_ig_api_timeout())
        response = requests.get(url, headers=self.authenticated_headers)
        if response.status_code != 200:
            logging.error("HTTP request returned {}".format(response.status_code))
            raise RuntimeError("HTTP request returned {}".format(response.status_code))
        data = json.loads(response.text)
        if "errorCode" in data:
            logging.error(data["errorCode"])
            raise RuntimeError(data["errorCode"])
        return data

    def get_macd(
        self, market: Market, interval: Interval, data_range: int
    ) -> MarketMACD:
        data = self._macd_dataframe(market, interval)
        # TODO Put date instead of index numbers
        return MarketMACD(
            market,
            data.index,
            data["MACD"].values,
            data["Signal"].values,
            data["Hist"].values,
        )

    def _macd_dataframe(self, market: Market, interval: Interval) -> pandas.DataFrame:
        prices = self.get_prices(market, Interval.DAY, 26)
        if prices is None:
            return None
        return Utils.macd_df_from_list(
            prices.dataframe[MarketHistory.CLOSE_COLUMN].values
        )
