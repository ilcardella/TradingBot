import os
import sys
import inspect
import pytest
import json
import pandas as pd

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,'{}/src'.format(parentdir))

from Strategies.WeightedAvgPeak import WeightedAvgPeak
from Utils import TradeDirection
from common.MockComponents import MockBroker, MockIG, MockAV

@pytest.fixture
def config():
    """
    Returns a dict with config parameter for strategy and simpleMACD
    """
    # Read configuration file
    try:
        with open('config/config.json', 'r') as file:
            config = json.load(file)
            config['general']['use_av_api'] = True
    except IOError:
        exit()
    return config


def test_find_trade_signal(config):
    services = {
        'ig_index': MockIG('test/test_data/mock_ig_market_info.json',
                                'test/test_data/mock_ig_historic_price.json'),
        'alpha_vantage': MockAV('test/test_data/mock_av_weekly.json')
    }
    broker = MockBroker(config, services)
    strategy = WeightedAvgPeak(config, broker)
    tradeDir, limit, stop = strategy.find_trade_signal('MOCK')

    assert tradeDir is not None
    assert limit is None
    assert stop is None

    assert tradeDir == TradeDirection.NONE
