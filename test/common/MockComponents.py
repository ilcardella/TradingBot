import os
import sys
import inspect
import json
import pandas as pd

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, "{}/src".format(parentdir))


class MockIG:
    """
    Mock broker interface class
    """

    def __init__(self, mockFilepath, mockPricesFilepath):
        self.mockFilepath = mockFilepath
        self.mockPricesFilepath = mockPricesFilepath
        pass

    def get_market_info(self, epic_id):
        # Read mock file
        try:
            with open(self.mockFilepath, "r") as file:
                mock = json.load(file)
        except IOError:
            exit()
        return mock

    def get_prices(self, epic_id, interval, data_range):
        # Read mock file
        try:
            with open(self.mockPricesFilepath, "r") as file:
                mock = json.load(file)
        except IOError:
            exit()
        return mock

    def macd_dataframe(self, epic, interval):
        data = [i + 1 for i in range(100)]
        px = pd.DataFrame({"close": data})
        px["26_ema"] = pd.DataFrame.ewm(px["close"], span=26).mean()
        px["12_ema"] = pd.DataFrame.ewm(px["close"], span=12).mean()
        px["MACD"] = px["12_ema"] - px["26_ema"]
        px["MACD_Signal"] = px["MACD"].rolling(9).mean()
        px["MACD_Hist"] = px["MACD"] - px["MACD_Signal"]
        return px


class MockAV:
    """
    Mock AlphaVantage interface class
    """

    def __init__(self, mockFilepath):
        self.mockFilepath = mockFilepath

    def macdext(self, marketId, interval):
        # Read mock file
        try:
            with open(self.mockFilepath, "r") as file:
                mock = json.load(file)
                px = pd.DataFrame.from_dict(
                    mock["Technical Analysis: MACDEXT"], orient="index", dtype=float
                )
                px.index = range(len(px))
        except IOError:
            exit()
        return px

    def weekly(self, marketId):
        # Read mock file
        try:
            with open(self.mockFilepath, "r") as file:
                mock = json.load(file)
                px = pd.DataFrame.from_dict(
                    mock["Weekly Time Series"], orient="index", dtype=float
                )
        except IOError:
            exit()
        return px


class MockBroker:
    """
    Mock Broker class
    """

    def __init__(self, config, services):
        self.ig = services["ig_index"]
        self.av = services["alpha_vantage"]
        self.use_av_api = config["alpha_vantage"]["enable"]
        self.mock_watchlist = [
            {"epic": "EPIC1"},
            {"epic": "EPIC2"},
            {"epic": "EPIC3"},
            {"epic": "EPIC4"},
        ]

    def get_market_info(self, epic):
        data = {}
        info = self.ig.get_market_info(epic)
        data["market_id"] = epic
        data["bid"] = info["snapshot"]["bid"]
        data["offer"] = info["snapshot"]["offer"]
        data["stop_distance_min"] = info["dealingRules"][
            "minNormalStopOrLimitDistance"
        ]["value"]
        data["epic"] = epic
        data["name"] = epic
        data["high"] = info["snapshot"]["high"]
        data["low"] = info["snapshot"]["low"]
        return data

    def get_prices(self, epic, market_id, interval, range):
        data = {"high": [], "low": [], "close": [], "volume": []}
        prices = self.ig.get_prices(epic, interval, range)
        for i in prices["prices"]:
            if i["highPrice"]["bid"] is not None:
                data["high"].append(i["highPrice"]["bid"])
            if i["lowPrice"]["bid"] is not None:
                data["low"].append(i["lowPrice"]["bid"])
            if i["closePrice"]["bid"] is not None:
                data["close"].append(i["closePrice"]["bid"])
            if isinstance(i["lastTradedVolume"], int):
                data["volume"].append(int(i["lastTradedVolume"]))
        return data

    def macd_dataframe(self, epic, market_id, interval):
        if self.use_av_api:
            return self.av.macdext(market_id, interval)
        else:
            return self.ig.macd_dataframe(epic, None)
        return None

    def weekly(self, market_id):
        return self.av.weekly(market_id)

    def get_market_from_watchlist(self, watchlist_name):
        return self.mock_watchlist
