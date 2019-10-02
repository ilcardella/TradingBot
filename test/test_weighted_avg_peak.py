import os
import sys
import inspect
import pytest
import json
import pandas as pd
from enum import Enum

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, "{}/src".format(parentdir))

from Strategies.WeightedAvgPeak import WeightedAvgPeak
from Utility.Utils import TradeDirection
from Interfaces.Market import Market
from Components.Broker import Broker
from Components.IGInterface import IGInterface
from Components.AVInterface import AVInterface
from common.MockRequests import (
    ig_request_login,
    ig_request_set_account,
    ig_request_market_info,
    ig_request_prices,
    ig_request_trade,
    ig_request_confirm_trade,
)

class Mock_Interval(Enum):
    MOCK="mock"


@pytest.fixture
def config():
    """
    Returns a dict with config parameter for strategy and simpleMACD
    """
    # Read configuration file
    try:
        with open("config/config.json", "r") as file:
            config = json.load(file)
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


def test_find_trade_signal(config, credentials, requests_mock):
    ig_request_login(requests_mock)
    ig_request_set_account(requests_mock)
    ig_request_market_info(requests_mock)
    ig_request_prices(requests_mock)
    ig_request_trade(requests_mock)
    ig_request_confirm_trade(requests_mock)

    services = {
        "ig_index": IGInterface(config, credentials),
        "alpha_vantage": AVInterface(credentials["av_api_key"], config),
    }
    broker = Broker(config, services)
    broker.use_av_api = False

    strategy = WeightedAvgPeak(config, broker)

    # Need to use a mock enum as the requests_mock expect "mock" as interval
    prices = broker.get_prices("mock", "mock", Mock_Interval.MOCK, "mock")
    market = create_mock_market(broker)
    tradeDir, limit, stop = strategy.find_trade_signal(market, prices)

    assert tradeDir is not None
    assert limit is None
    assert stop is None

    assert tradeDir == TradeDirection.NONE
