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
from common.MockComponents import MockBroker, MockIG, MockAV


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
    except IOError:
        exit()
    return config


@pytest.fixture
def strategy(config):
    """
    Initialise the strategy with mock services
    """
    services = {
        "ig_index": MockIG(
            "test/test_data/mock_ig_market_info.json",
            "test/test_data/mock_ig_historic_price.json",
        ),
        "alpha_vantage": MockAV("test/test_data/mock_macdext_buy.json"),
    }
    broker = MockBroker(config, services)
    return SimpleMACD(config, broker)


def create_mock_market(broker):
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


def test_find_trade_signal_buy(config):
    services = {
        "ig_index": MockIG(
            "test/test_data/mock_ig_market_info.json",
            "test/test_data/mock_ig_historic_price.json",
        ),
        "alpha_vantage": MockAV("test/test_data/mock_macdext_buy.json"),  # BUY json
    }
    broker = MockBroker(config, services)
    strategy = SimpleMACD(config, broker)
    data = broker.macd_dataframe("", "", "")

    # Create a mock market data from the json file
    market = create_mock_market(broker)

    # Call function to test
    tradeDir, limit, stop = strategy.find_trade_signal(market, data)

    assert tradeDir is not None
    assert limit is not None
    assert stop is not None

    assert tradeDir == TradeDirection.BUY


def test_find_trade_signal_sell(config):
    services = {
        "ig_index": MockIG(
            "test/test_data/mock_ig_market_info.json",
            "test/test_data/mock_ig_historic_price.json",
        ),
        "alpha_vantage": MockAV("test/test_data/mock_macdext_sell.json"),  # SELL json
    }
    broker = MockBroker(config, services)
    strategy = SimpleMACD(config, broker)
    data = broker.macd_dataframe("", "", "")

    # Create a mock market data from the json file
    market = create_mock_market(broker)

    tradeDir, limit, stop = strategy.find_trade_signal(market, data)

    assert tradeDir is not None
    assert limit is not None
    assert stop is not None

    assert tradeDir == TradeDirection.SELL


def test_find_trade_signal_hold(config):
    services = {
        "ig_index": MockIG(
            "test/test_data/mock_ig_market_info.json",
            "test/test_data/mock_ig_historic_price.json",
        ),
        "alpha_vantage": MockAV("test/test_data/mock_macdext_hold.json"),  # HOLD json
    }
    broker = MockBroker(config, services)
    strategy = SimpleMACD(config, broker)
    data = broker.macd_dataframe("", "", "")

    # Create a mock market data from the json file
    market = create_mock_market(broker)

    tradeDir, limit, stop = strategy.find_trade_signal(market, data)

    assert tradeDir is not None
    assert limit is None
    assert stop is None

    assert tradeDir == TradeDirection.NONE


def test_find_trade_signal_exception(config):
    # TODO provide wrong data and assert exception thrown
    assert True


def test_calculate_stop_limit(strategy):

    limit, stop = strategy.calculate_stop_limit(TradeDirection.BUY, 100, 100, 10, 10)
    assert limit == 110
    assert stop == 90

    limit, stop = strategy.calculate_stop_limit(TradeDirection.SELL, 100, 100, 10, 10)
    assert limit == 90
    assert stop == 110

    limit, stop = strategy.calculate_stop_limit(TradeDirection.NONE, 100, 100, 10, 10)
    assert limit is None
    assert stop is None


def test_generate_signals_from_dataframe(strategy):
    px = strategy.broker.macd_dataframe("mock", "mock", "mock")
    px = strategy.generate_signals_from_dataframe(px)

    assert "positions" in px
    assert len(px) > 26
    # TODO add more checks


def test_get_trade_direction_from_signals(strategy):
    dataframe = strategy.broker.macd_dataframe("mock", "mock", "mock")
    dataframe = strategy.generate_signals_from_dataframe(dataframe)
    tradeDir = strategy.get_trade_direction_from_signals(dataframe)

    # BUY becasue the strategy fixture loads the buy test json
    assert tradeDir == TradeDirection.BUY


def test_backtest(config):
    services = {
        "ig_index": MockIG(
            "test/test_data/mock_ig_market_info.json",
            "test/test_data/mock_ig_historic_price.json",
        ),
        "alpha_vantage": MockAV("test/test_data/mock_macdext_buy.json"),
    }
    broker = MockBroker(config, services)
    strategy = SimpleMACD(config, broker)

    # Create a mock market data from the json file
    market = create_mock_market(broker)

    result = strategy.backtest(
        market,
        dt.strptime("2018-01-01", "%Y-%m-%d"),
        dt.strptime("2018-06-01", "%Y-%m-%d"),
    )

    assert 'balance' in result
    assert result['balance'] is not None
    assert result['balance'] == 997.9299999999998
    assert 'trades' in result
    assert len(result['trades']) == 8

