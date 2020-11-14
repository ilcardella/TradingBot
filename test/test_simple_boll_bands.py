from pathlib import Path

import pytest
from common.MockRequests import (
    av_request_macd_ext,
    av_request_prices,
    ig_request_account_details,
    ig_request_confirm_trade,
    ig_request_login,
    ig_request_market_info,
    ig_request_navigate_market,
    ig_request_open_positions,
    ig_request_prices,
    ig_request_search_market,
    ig_request_set_account,
    ig_request_trade,
    ig_request_watchlist,
)

from tradingbot.components import Configuration, TradeDirection
from tradingbot.components.broker import Broker, BrokerFactory
from tradingbot.strategies import SimpleBollingerBands


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
    config = Configuration.from_filepath(Path("test/test_data/trading_bot.toml"))
    config.config["strategies"]["active"] = "simple_boll_bands"
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
    av_request_prices(requests_mock, data="av_daily_boll_bands_buy.json")
    strategy = SimpleBollingerBands(config, broker)
    # Create a mock market data from the json file
    market = create_mock_market(broker)
    # Call function to test
    data = strategy.fetch_datapoints(market)
    tradeDir, limit, stop = strategy.find_trade_signal(market, data)

    assert tradeDir is not None
    assert limit is not None
    assert stop is not None

    assert tradeDir == TradeDirection.BUY
    assert (
        limit
        == market.offer
        + market.offer
        * config.config["strategies"]["simple_boll_bands"]["limit_perc"]
        / 100
    )
    assert (
        stop
        == market.bid
        - market.bid
        * config.config["strategies"]["simple_boll_bands"]["stop_perc"]
        / 100
    )


def test_find_trade_signal_sell(config, broker, requests_mock):
    av_request_prices(requests_mock, data="av_daily_boll_bands_sell.json")
    strategy = SimpleBollingerBands(config, broker)
    # Create a mock market data from the json file
    market = create_mock_market(broker)
    data = strategy.fetch_datapoints(market)
    tradeDir, limit, stop = strategy.find_trade_signal(market, data)

    assert tradeDir is TradeDirection.NONE
    assert limit is None
    assert stop is None


def test_find_trade_signal_hold(config, broker, requests_mock):
    av_request_prices(requests_mock)
    strategy = SimpleBollingerBands(config, broker)
    # Create a mock market data from the json file
    market = create_mock_market(broker)
    data = strategy.fetch_datapoints(market)
    tradeDir, limit, stop = strategy.find_trade_signal(market, data)

    assert tradeDir is not None
    assert limit is None
    assert stop is None

    assert tradeDir == TradeDirection.NONE
