import requests
import json
import logging
import os
import inspect
import sys
from enum import Enum
import numpy
import pandas as pd

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from Utility.Utils import Utils, TradeDirection


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


class IGInterface:
    """
    IG broker interface class, provides functions to use the IG REST API
    """

    def __init__(self, config, credentials):
        self.read_configuration(config)
        demoPrefix = IG_API_URL.DEMO_PREFIX.value if self.useDemo else ""
        self.apiBaseURL = IG_API_URL.BASE_URI.value.replace("@", demoPrefix)
        self.authenticated_headers = {}
        if self.paperTrading:
            logging.info("Paper trading is active")
        if not self.authenticate(credentials):
            logging.error("Authentication failed")
            exit()
        logging.info("IG initialised.")

    def read_configuration(self, config):
        """
        Read the configuration from the config json
        """
        self.useDemo = config["ig_interface"]["use_demo_account"]
        self.orderType = config["ig_interface"]["order_type"]
        self.orderSize = config["ig_interface"]["order_size"]
        self.orderExpiry = config["ig_interface"]["order_expiry"]
        self.useGStop = config["ig_interface"]["use_g_stop"]
        self.orderCurrency = config["ig_interface"]["order_currency"]
        self.orderForceOpen = config["ig_interface"]["order_force_open"]
        self.paperTrading = config["ig_interface"]["paper_trading"]

    def authenticate(self, credentials):
        """
        Authenticate the IGInterface instance with the given credentials

            - **credentials**: json object containing username, passowrd, default account and api key
            - Returns **False** if an error occurs otherwise True
        """
        data = {
            "identifier": credentials["username"],
            "password": credentials["password"],
        }
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json; charset=utf-8",
            "X-IG-API-KEY": credentials["api_key"],
            "Version": "2",
        }
        url = "{}/{}".format(self.apiBaseURL, IG_API_URL.SESSION.value)
        response = requests.post(url, data=json.dumps(data), headers=headers)

        if response.status_code != 200:
            return False

        headers_json = dict(response.headers)
        try:
            CST_token = headers_json["CST"]
            x_sec_token = headers_json["X-SECURITY-TOKEN"]
        except:
            return False

        self.authenticated_headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json; charset=utf-8",
            "X-IG-API-KEY": credentials["api_key"],
            "CST": CST_token,
            "X-SECURITY-TOKEN": x_sec_token,
        }

        self.set_default_account(credentials["account_id"])
        return True

    def set_default_account(self, accountId):
        """
        Sets the IG account to use

            - **accountId**: String representing the accound id to use
            - Returns **False** if an error occurs otherwise True
        """
        url = "{}/{}".format(self.apiBaseURL, IG_API_URL.SESSION.value)
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
        url = "{}/{}".format(self.apiBaseURL, IG_API_URL.ACCOUNTS.value)
        d = self.http_get(url)
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
        url = "{}/{}".format(self.apiBaseURL, IG_API_URL.POSITIONS.value)
        return self.http_get(url)

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
        url = "{}/{}/{}".format(self.apiBaseURL, IG_API_URL.MARKETS.value, epic_id)
        market = self.http_get(url)
        return market

    def search_market(self, search):
        """
        Returns a list of markets that matched the search string
        """
        url = "{}/{}?searchTerm={}".format(
            self.apiBaseURL, IG_API_URL.MARKETS.value, search
        )
        markets = self.http_get(url)
        if markets is not None and 'markets' in markets:
            return markets['markets']
        return markets

    def get_prices(self, epic_id, interval, data_range):
        """
        Returns past prices for the given epic

            - **epic_id**: market epic as string
            - **interval**: resolution of the time series: minute, hours, etc.
            - **data_range**: amount of datapoint to fetch
            - Returns **None** if an error occurs otherwise the json object returned by IG API
        """
        url = "{}/{}/{}/{}/{}".format(
            self.apiBaseURL, IG_API_URL.PRICES.value, epic_id, interval, data_range
        )
        d = self.http_get(url)
        if d is not None and "allowance" in d:
            remaining_allowance = d["allowance"]["remainingAllowance"]
            reset_time = Utils.humanize_time(int(d["allowance"]["allowanceExpiry"]))
            if remaining_allowance < 100:
                logging.warn(
                    "Remaining API calls left: {}".format(str(remaining_allowance))
                )
                logging.warn("Time to API Key reset: {}".format(str(reset_time)))
        return d

    def trade(self, epic_id, trade_direction, limit, stop):
        """
        Try to open a new trade for the given epic

            - **epic_id**: market epic as string
            - **trade_direction**: BUY or SELL
            - **limit**: limit level
            - **stop**: stop level
            - Returns **False** if an error occurs otherwise True
        """
        if self.paperTrading:
            logging.info(
                "Paper trade: {} {} with limit={} and stop={}".format(
                    trade_direction, epic_id, limit, stop
                )
            )
            return True

        url = "{}/{}".format(self.apiBaseURL, IG_API_URL.POSITIONS_OTC.value)
        data = {
            "direction": trade_direction,
            "epic": epic_id,
            "limitLevel": limit,
            "orderType": self.orderType,
            "size": self.orderSize,
            "expiry": self.orderExpiry,
            "guaranteedStop": self.useGStop,
            "currencyCode": self.orderCurrency,
            "forceOpen": self.orderForceOpen,
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
                    trade_direction, epic_id, limit, stop
                )
            )
            return True
        else:
            logging.warning(
                "Trade {} of {} has failed!".format(trade_direction, epic_id)
            )
            return False

    def confirm_order(self, dealRef):
        """
        Confirm an order from a dealing reference

            - **dealRef**: dealing reference to confirm
            - Returns **False** if an error occurs otherwise True
        """
        url = "{}/{}/{}".format(self.apiBaseURL, IG_API_URL.CONFIRMS.value, dealRef)
        d = self.http_get(url)

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
        if self.paperTrading:
            logging.info(
                "Paper trade: close {} position".format(
                    position["market"]["instrumentName"]
                )
            )
            return True
        # To close we need the opposite direction
        direction = TradeDirection.NONE
        if position["position"]["direction"] == TradeDirection.BUY.name:
            direction = TradeDirection.SELL.name
        elif position["position"]["direction"] == TradeDirection.SELL.name:
            direction = TradeDirection.BUY.name
        else:
            logging.error("Wrong position direction!")
            return False

        url = "{}/{}".format(self.apiBaseURL, IG_API_URL.POSITIONS_OTC.value)
        data = {
            "dealId": position["position"]["dealId"],
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
            logging.info(
                "Position  for {} closed".format(position["market"]["instrumentName"])
            )
            return True
        else:
            logging.error(
                "Could not close position for {}".format(
                    position["market"]["instrumentName"]
                )
            )
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
                for p in positions["positions"]:
                    try:
                        if not self.close_position(p):
                            result = False
                    except:
                        logging.error(
                            "Error closing position for {}".format(
                                p["market"]["instrumentName"]
                            )
                        )
                        result = False
            else:
                logging.error("Unable to retrieve open positions!")
                result = False
        except:
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
        url = "{}/{}/{}".format(self.apiBaseURL, IG_API_URL.MARKET_NAV.value, node_id)
        data = self.http_get(url)
        return data if data is not None else None

    def get_watchlist(self, id):
        """
        Get the watchlist info

            - **id**: id of the watchlist. If empty id is provided, the
              function returns the list of all the watchlist in the account
        """
        url = "{}/{}/{}".format(self.apiBaseURL, IG_API_URL.WATCHLISTS.value, id)
        data = self.http_get(url)
        return data if data is not None else None

    def get_markets_from_watchlist(self, name):
        """
        Get the list of markets included in the watchlist

            - **name**: name of the watchlist
        """
        markets = []
        # Request with empty name returns list of all the watchlists
        all_watchlists = self.get_watchlist("")
        if all_watchlists is not None:
            for w in all_watchlists["watchlists"]:
                if "name" in w and w["name"] == name:
                    data = self.get_watchlist(w["id"])
                    if data is not None and "markets" in data:
                        return data["markets"]
        return None

    def http_get(self, url):
        """
        Perform an HTTP GET request to the url.
        Return the json object returned from the API if 200 is received
        Return None if an error is received from the API
        """
        try:
            response = requests.get(url, headers=self.authenticated_headers)
            if response.status_code != 200:
                return None

            data = json.loads(response.text)

            if "errorCode" in data:
                logging.error(data["errorCode"])
                return None
            else:
                return data
        except:
            return None

    def macd_dataframe(self, epic, interval):
        """
        Return a datafram with MACD data for the requested market
        """
        prices = self.get_prices(epic, "DAY", 26)
        if prices is None:
            return None
        # Prepare data
        prevBid = 0
        hist_data = []
        for p in prices["prices"]:
            if p["closePrice"]["bid"] is None:
                hist_data.append(prevBid)
            else:
                hist_data.append(p["closePrice"]["bid"])
                prevBid = p["closePrice"]["bid"]
        # Calculate the MACD indicator
        px = pd.DataFrame({"close": hist_data})
        px["26_ema"] = pd.DataFrame.ewm(px["close"], span=26).mean()
        px["12_ema"] = pd.DataFrame.ewm(px["close"], span=12).mean()
        px["MACD"] = px["12_ema"] - px["26_ema"]
        px["MACD_Signal"] = px["MACD"].rolling(9).mean()
        px["MACD_Hist"] = px["MACD"] - px["MACD_Signal"]
        return px
