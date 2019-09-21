import os
import sys
import inspect
import pytest
import json
import pandas as pd

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, "{}/src".format(parentdir))

from Strategies.WeightedAvgPeak import WeightedAvgPeak
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


def create_mock_market(broker):
    data = broker.get_market_info("mock")
    market = Market()
    market.epic = data['epic']
    market.id = data['market_id']
    market.name = data['name']
    market.bid = data['bid']
    market.offer = data['offer']
    market.high = data['high']
    market.low = data['low']
    market.stop_distance_min = data['stop_distance_min']
    return market


def test_find_trade_signal(config):
    services = {
        "ig_index": MockIG(
            "test/test_data/mock_ig_market_info.json",
            "test/test_data/mock_ig_historic_price.json",
        ),
        "alpha_vantage": MockAV("test/test_data/mock_av_weekly.json"),
    }
    broker = MockBroker(config, services)
    strategy = WeightedAvgPeak(config, broker)
    broker.use_av_api = False
    prices = broker.get_prices("", "", "", "")

    market = create_mock_market(broker)

    tradeDir, limit, stop = strategy.find_trade_signal(market, prices)

    assert tradeDir is not None
    assert limit is None
    assert stop is None

    assert tradeDir == TradeDirection.NONE
