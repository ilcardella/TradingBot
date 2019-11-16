import os
import sys
import inspect
import pytest
import json
from datetime import datetime as dt
import pandas as pd

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, "{}/src".format(parentdir))

from Strategies.SimpleMACD import SimpleMACD
from Utility.Utils import TradeDirection
from Interfaces.Market import Market
from Components.Broker import Broker, Interval
from Components.IGInterface import IGInterface
from Components.AVInterface import AVInterface
from common.MockRequests import (
    ig_request_login,
    ig_request_set_account,
    ig_request_market_info,
    ig_request_prices,
    av_request_macd_ext,
    av_request_prices,
)


@pytest.fixture
def config():
    """
    Returns a dict with config parameter for strategy and simpleMACD
    """
    # Read configuration file
    try:
        with open("config/config.json", "r") as file:
            config = json.load(file)
            config["alpha_vantage"]["enable"] = True
            config["alpha_vantage"]["api_timeout"] = 0
    except IOError:
        exit()
    return config


@pytest.fixture
def credentials():
    """
    Returns a dict with credentials parameters
    """
    return {
        "username": "user",
        "password": "pwd",
        "api_key": "12345",
        "account_id": "12345",
        "av_api_key": "12345",
    }


@pytest.fixture
def broker(config, credentials, requests_mock):
    """
    Initialise the strategy with mock services
    """
    ig_request_login(requests_mock)
    ig_request_set_account(requests_mock)
    services = {
        "ig_index": IGInterface(config, credentials),
        "alpha_vantage": AVInterface(credentials["av_api_key"], config),
    }
    return Broker(config, services)


def create_mock_market(broker, requests_mock):
    ig_request_market_info(requests_mock)
    data = broker.get_market_info("mock")
    market = Market()
    market.epic = data["epic"]
    market.id = data["market_id"]
    market.name = data["name"]
    market.bid = data["bid"]
    market.offer = data["offer"]
    market.high = data["high"]
    market.low = data["low"]
    market.stop_distance_min = data["stop_distance_min"]
    return market


def datafram_from_json(filepath):
    """Load a json file and return a dataframe"""
    try:
        with open(filepath, "r") as file:
            px = pd.DataFrame.from_dict(
                json.load(file)["Technical Analysis: MACDEXT"],
                orient="index",
                dtype=float,
            )
            px.index = pd.to_datetime(px.index)
            return px
    except IOError:
        exit()


def test_find_trade_signal_buy(config, broker, requests_mock):
    strategy = SimpleMACD(config, broker)
    data = datafram_from_json("test/test_data/alpha_vantage/mock_macd_ext_buy.json")
    # Create a mock market data from the json file
    market = create_mock_market(broker, requests_mock)
    # Call function to test
    tradeDir, limit, stop = strategy.find_trade_signal(market, data)

    assert tradeDir is not None
    assert limit is not None
    assert stop is not None

    assert tradeDir == TradeDirection.BUY


def test_find_trade_signal_sell(config, broker, requests_mock):
    strategy = SimpleMACD(config, broker)
    data = datafram_from_json("test/test_data/alpha_vantage/mock_macd_ext_sell.json")
    # Create a mock market data from the json file
    market = create_mock_market(broker, requests_mock)
    tradeDir, limit, stop = strategy.find_trade_signal(market, data)

    assert tradeDir is not None
    assert limit is not None
    assert stop is not None

    assert tradeDir == TradeDirection.SELL


def test_find_trade_signal_hold(config, broker, requests_mock):
    strategy = SimpleMACD(config, broker)
    data = datafram_from_json("test/test_data/alpha_vantage/mock_macd_ext_hold.json")
    # Create a mock market data from the json file
    market = create_mock_market(broker, requests_mock)

    tradeDir, limit, stop = strategy.find_trade_signal(market, data)

    assert tradeDir is not None
    assert limit is None
    assert stop is None

    assert tradeDir == TradeDirection.NONE


def test_find_trade_signal_exception(config):
    # TODO provide wrong data and assert exception thrown
    assert True


def test_calculate_stop_limit(config, broker):
    strategy = SimpleMACD(config, broker)
    limit, stop = strategy.calculate_stop_limit(TradeDirection.BUY, 100, 100, 10, 10)
    assert limit == 110
    assert stop == 90

    limit, stop = strategy.calculate_stop_limit(TradeDirection.SELL, 100, 100, 10, 10)
    assert limit == 90
    assert stop == 110

    limit, stop = strategy.calculate_stop_limit(TradeDirection.NONE, 100, 100, 10, 10)
    assert limit is None
    assert stop is None


def test_generate_signals_from_dataframe(config, broker):
    strategy = SimpleMACD(config, broker)
    data = datafram_from_json("test/test_data/alpha_vantage/mock_macd_ext_hold.json")
    px = strategy.generate_signals_from_dataframe(data)

    assert "positions" in px
    assert len(px) > 26
    # TODO add more checks


def test_get_trade_direction_from_signals(config, broker, requests_mock):
    strategy = SimpleMACD(config, broker)
    data = datafram_from_json("test/test_data/alpha_vantage/mock_macd_ext_buy.json")
    dataframe = strategy.generate_signals_from_dataframe(data)
    tradeDir = strategy.get_trade_direction_from_signals(dataframe)

    # BUY becasue the mock response loads the buy test json
    assert tradeDir == TradeDirection.BUY


def test_backtest(config, broker, requests_mock):
    av_request_macd_ext(requests_mock, data="mock_macd_ext_buy.json")
    av_request_prices(requests_mock)

    strategy = SimpleMACD(config, broker)

    # Create a mock market data from the json file
    market = create_mock_market(broker, requests_mock)

    result = strategy.backtest(
        market,
        dt.strptime("2018-01-01", "%Y-%m-%d"),
        dt.strptime("2018-06-01", "%Y-%m-%d"),
    )

    assert "balance" in result
    assert result["balance"] is not None
    assert result["balance"] == 997.9299999999998
    assert "trades" in result
    assert len(result["trades"]) == 8

