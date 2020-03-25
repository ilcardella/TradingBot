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

from Components.Configuration import Configuration
from Strategies.SimpleMACD import SimpleMACD
from Components.Utils import TradeDirection
from Interfaces.Market import Market
from Interfaces.MarketMACD import MarketMACD
from Components.Broker.Broker import Broker
from Components.Broker.BrokerFactory import BrokerFactory
from common.MockRequests import (
    ig_request_login,
    ig_request_set_account,
    ig_request_account_details,
    ig_request_open_positions,
    ig_request_market_info,
    ig_request_search_market,
    ig_request_prices,
    ig_request_trade,
    ig_request_confirm_trade,
    ig_request_navigate_market,
    ig_request_watchlist,
    av_request_prices,
    av_request_macd_ext,
)


@pytest.fixture
def mock_http_calls(requests_mock):
    ig_request_login(requests_mock)
    ig_request_set_account(requests_mock)
    ig_request_account_details(requests_mock)
    ig_request_open_positions(requests_mock)
    ig_request_market_info(requests_mock)
    ig_request_search_market(requests_mock)
    ig_request_prices(requests_mock)
    ig_request_trade(requests_mock)
    ig_request_confirm_trade(requests_mock)
    ig_request_navigate_market(requests_mock)
    ig_request_navigate_market(
        requests_mock, args="668394", data="mock_navigate_markets_markets.json"
    )
    ig_request_navigate_market(
        requests_mock, args="77976799", data="mock_navigate_markets_markets.json"
    )
    ig_request_navigate_market(
        requests_mock, args="89291253", data="mock_navigate_markets_markets.json"
    )
    ig_request_watchlist(requests_mock)
    ig_request_watchlist(requests_mock, args="12345678", data="mock_watchlist.json")
    av_request_prices(requests_mock)
    av_request_macd_ext(requests_mock)


@pytest.fixture
def config():
    config = Configuration.from_filepath("test/test_data/config.json")
    config.config["strategies"]["active"] = "simple_macd"
    config.config["stocks_interface"]["active"] = "alpha_vantage"
    config.config["stocks_interface"]["alpha_vantage"]["api_timeout"] = 0
    return config


@pytest.fixture
def broker(config, mock_http_calls):
    """
    Initialise the strategy with mock services
    """
    return Broker(BrokerFactory(config))


def create_mock_market(broker):
    return broker.get_market_info("mock")


def test_find_trade_signal_buy(config, broker, requests_mock):
    av_request_macd_ext(
        requests_mock, data="mock_macd_ext_buy.json"
    )
    strategy = SimpleMACD(config, broker)
    # Create a mock market data from the json file
    market = create_mock_market(broker)
    # Call function to test
    data = strategy.fetch_datapoints(market)
    tradeDir, limit, stop = strategy.find_trade_signal(market, data)

    assert tradeDir is not None
    assert limit is not None
    assert stop is not None

    assert tradeDir == TradeDirection.BUY


def test_find_trade_signal_sell(config, broker, requests_mock):
    av_request_macd_ext(
        requests_mock, data="mock_macd_ext_sell.json"
    )
    strategy = SimpleMACD(config, broker)
    # Create a mock market data from the json file
    market = create_mock_market(broker)
    data = strategy.fetch_datapoints(market)
    tradeDir, limit, stop = strategy.find_trade_signal(market, data)

    assert tradeDir is not None
    assert limit is not None
    assert stop is not None

    assert tradeDir == TradeDirection.SELL


def test_find_trade_signal_hold(config, broker, requests_mock):
    av_request_macd_ext(
        requests_mock, data="mock_macd_ext_hold.json"
    )
    strategy = SimpleMACD(config, broker)
    # Create a mock market data from the json file
    market = create_mock_market(broker)
    data = strategy.fetch_datapoints(market)
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


def test_generate_signals_from_dataframe(config, broker, requests_mock):
    av_request_macd_ext(
        requests_mock, data="mock_macd_ext_hold.json"
    )
    strategy = SimpleMACD(config, broker)
    data = strategy.fetch_datapoints(create_mock_market(broker))
    px = strategy.generate_signals_from_dataframe(data.dataframe)

    assert "positions" in px
    assert len(px) > 26
    # TODO add more checks


def test_get_trade_direction_from_signals(config, broker, requests_mock):
    av_request_macd_ext(
        requests_mock, data="mock_macd_ext_buy.json"
    )
    strategy = SimpleMACD(config, broker)
    data = strategy.fetch_datapoints(create_mock_market(broker))
    dataframe = strategy.generate_signals_from_dataframe(data.dataframe)
    tradeDir = strategy.get_trade_direction_from_signals(dataframe)

    # BUY becasue the mock response loads the buy test json
    assert tradeDir == TradeDirection.BUY


# TODO
# def test_backtest(config, broker, requests_mock):
#     ig_request_market_info(requests_mock)
#     ig_request_prices(requests_mock)
#     # av_request_macd_ext(requests_mock, data="mock_macd_ext_buy.json")
#     # av_request_prices(requests_mock)

#     strategy = SimpleMACD(config, broker)

#     # Create a mock market data from the json file
#     market = create_mock_market(broker, requests_mock)

#     result = strategy.backtest(
#         market,
#         dt.strptime("2018-01-01", "%Y-%m-%d"),
#         dt.strptime("2018-06-01", "%Y-%m-%d"),
#     )

#     assert "balance" in result
#     assert result["balance"] is not None
#     assert result["balance"] == 997.9299999999998
#     assert "trades" in result
#     assert len(result["trades"]) == 8
