from pathlib import Path

import pytest
from common.MockRequests import (
    ig_request_confirm_trade,
    ig_request_login,
    ig_request_market_info,
    ig_request_prices,
    ig_request_set_account,
    ig_request_trade,
)

from tradingbot.components import Configuration, TradeDirection
from tradingbot.components.broker import Broker, BrokerFactory
from tradingbot.strategies import WeightedAvgPeak


@pytest.fixture
def config():
    config = Configuration.from_filepath(Path("test/test_data/trading_bot.toml"))
    config.config["strategies"]["active"] = "weighted_avg_peak"
    return config


@pytest.fixture
def broker(config, requests_mock):
    """
    Initialise the strategy with mock services
    """
    ig_request_login(requests_mock)
    ig_request_set_account(requests_mock)
    return Broker(BrokerFactory(config))


def test_find_trade_signal(config, broker, requests_mock):
    ig_request_login(requests_mock)
    ig_request_set_account(requests_mock)
    ig_request_prices(requests_mock)
    ig_request_trade(requests_mock)
    ig_request_confirm_trade(requests_mock)
    ig_request_market_info(requests_mock)

    strategy = WeightedAvgPeak(config, broker)

    # Need to use a mock enum as the requests_mock expect "mock" as interval
    market = broker.get_market_info("mock")
    prices = strategy.fetch_datapoints(market)
    tradeDir, limit, stop = strategy.find_trade_signal(market, prices)

    assert tradeDir is not None
    assert limit is None
    assert stop is None

    assert tradeDir == TradeDirection.NONE
