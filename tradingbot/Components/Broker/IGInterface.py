import requests
import json
import logging
from enum import Enum


from Components.Utils import Utils, TradeDirection
from Interfaces.MarketHistory import MarketHistory
from Interfaces.MarketMACD import MarketMACD
from Interfaces.Position import Position
from Interfaces.Market import Market
from .AbstractInterfaces import AccountInterface, StocksInterface


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

    def initialise(self):
        logging.info("initialising IGInterface...")
        demoPrefix = (
            IG_API_URL.DEMO_PREFIX.value
            if self._config.get_ig_use_demo_account()
            else ""
        )
        self.api_base_url = IG_API_URL.BASE_URI.value.replace("@", demoPrefix)
        self.authenticated_headers = {}
        if self._config.get_ig_paper_trading():
            logging.info("Paper trading is active")
        if not self.authenticate():
            logging.error("Authentication failed")
            raise RuntimeError("Unable to authenticate to IG Index. Check credentials")

    def authenticate(self):
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

    def set_default_account(self, accountId):
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

        logging.info("Using default account: {}".format(accountId))
        return True

    def get_account_balances(self):
        """
        Returns a tuple (balance, deposit) for the account in use

            - Returns **(None,None)** if an error occurs otherwise (balance, deposit)
        """
        url = "{}/{}".format(self.api_base_url, IG_API_URL.ACCOUNTS.value)
        d = self._http_get(url)
        if d is not None:
            for i in d["accounts"]:
                if str(i["accountType"]) == "SPREADBET":
                    balance = i["balance"]["balance"]
                    deposit = i["balance"]["deposit"]
                    return balance, deposit
        else:
            return None, None

    def get_open_positions(self):
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

    def get_positions_map(self):
        """
        Returns a *dict* containing the account open positions in the form
        {string: int} where the string is defined as 'marketId-tradeDirection' and
        the int is the trade size

            - Returns **None** if an error occurs otherwise a dict(string:int)
        """
        positionMap = {}
        position_json = self.get_open_positions()
        if position_json is not None:
            for item in position_json["positions"]:
                direction = item["position"]["direction"]
                dealSize = item["position"]["dealSize"]
                ccypair = item["market"]["epic"]
                key = ccypair + "-" + direction
                if key in positionMap:
                    positionMap[key] = dealSize + positionMap[key]
                else:
                    positionMap[key] = dealSize
            return positionMap
        else:
            return None

    def get_market_info(self, epic_id):
        """
        Returns info for the given market including a price snapshot

            - **epic_id**: market epic as string
            - Returns **None** if an error occurs otherwise the json returned by IG API
        """
        url = "{}/{}/{}".format(self.api_base_url, IG_API_URL.MARKETS.value, epic_id)
        info = self._http_get(url)

        if info is None or "markets" in info:
            # TODO raise exception
            return None
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
        return market

    def search_market(self, search):
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

    def get_prices(self, market, interval, data_range):
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
            volumes.append(int(price["lastTradedVolume"]))
        history = MarketHistory(market, dates, highs, lows, closes, volumes)
        return history

    def trade(self, epic_id, trade_direction, limit, stop):
        """
        Try to open a new trade for the given epic

            - **epic_id**: market epic as string
            - **trade_direction**: BUY or SELL
            - **limit**: limit level
            - **stop**: stop level
            - Returns **False** if an error occurs otherwise True
        """
        if self._config.get_ig_paper_trading():
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

    def confirm_order(self, dealRef):
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

    def close_position(self, position):
        """
        Close the given market position

            - **position**: position json object obtained from IG API
            - Returns **False** if an error occurs otherwise True
        """
        if self._config.get_ig_paper_trading():
            logging.info("Paper trade: close {} position".format(position.epic))
            return True
        # To close we need the opposite direction
        direction = TradeDirection.NONE
        if position.direction == TradeDirection.BUY:
            direction = TradeDirection.SELL.name
        elif position.direction == TradeDirection.SELL:
            direction = TradeDirection.BUY.name
        else:
            logging.error("Wrong position direction!")
            return False

        url = "{}/{}".format(self.api_base_url, IG_API_URL.POSITIONS_OTC.value)
        data = {
            "dealId": position.deal_id,
            "epic": None,
            "expiry": None,
            "direction": direction,
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

    def close_all_positions(self):
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
                            "Error closing position for {}".format(
                                p["market"]["instrumentName"]
                            )
                        )
                        result = False
            else:
                logging.error("Unable to retrieve open positions!")
                result = False
        except Exception:
            logging.error("Error during close all positions")
            result = False
        return result

    def get_account_used_perc(self):
        """
        Fetch the percentage of available balance is currently used

            - Returns the percentage of account used over total available amount
        """
        balance, deposit = self.get_account_balances()
        if balance is None or deposit is None:
            return None
        return Utils.percentage(deposit, balance)

    def navigate_market_node(self, node_id):
        """
        Navigate the market node id

            - Returns the json representing the market node
        """
        url = "{}/{}/{}".format(self.api_base_url, IG_API_URL.MARKET_NAV.value, node_id)
        data = self._http_get(url)
        return data if data is not None else None

    def _get_watchlist(self, id):
        """
        Get the watchlist info

            - **id**: id of the watchlist. If empty id is provided, the
              function returns the list of all the watchlist in the account
        """
        url = "{}/{}/{}".format(self.api_base_url, IG_API_URL.WATCHLISTS.value, id)
        data = self._http_get(url)
        return data if data is not None else None

    def get_markets_from_watchlist(self, name):
        """
        Get the list of markets included in the watchlist

            - **name**: name of the watchlist
        """
        markets = []
        # Request with empty name returns list of all the watchlists
        all_watchlists = self._get_watchlist("")
        if all_watchlists is not None:
            for w in all_watchlists["watchlists"]:
                if "name" in w and w["name"] == name:
                    data = self._get_watchlist(w["id"])
                    if data is not None and "markets" in data:
                        for m in data["markets"]:
                            markets.append(self.get_market_info(m["epic"]))
                    break
        return markets

    def _http_get(self, url):
        """
        Perform an HTTP GET request to the url.
        Return the json object returned from the API if 200 is received
        Return None if an error is received from the API
        """
        response = requests.get(url, headers=self.authenticated_headers)
        if response.status_code != 200:
            logging.error("HTTP request returned {}".format(response.status_code))
            raise RuntimeError("HTTP request returned {}".format(response.status_code))
        data = json.loads(response.text)
        if "errorCode" in data:
            logging.error(data["errorCode"])
            raise RuntimeError(data["errorCode"])
        return data

    def get_macd(self, market, interval, data_range):
        data = self._macd_dataframe(market, interval)
        # TODO Put date instead of index numbers
        return MarketMACD(
            market,
            range(len(data)),
            data["MACD"].values,
            data["Signal"].values,
            data["Hist"].values,
        )

    def _macd_dataframe(self, market, interval):
        prices = self.get_prices(market, "DAY", 26)
        if prices is None:
            return None
        return Utils.macd_df_from_list(
            prices.dataframe[MarketHistory.CLOSE_COLUMN].values
        )
