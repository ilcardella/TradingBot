import os
import sys
import inspect
import pytest
import json

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,'{}/src'.format(parentdir))

from Strategies.WeightedAvgPeak import WeightedAvgPeak
from Utils import TradeDirection

class MockBroker:
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
            with open(self.mockFilepath, 'r') as file:
                mock = json.load(file)
        except IOError:
            exit()
        return mock

    def get_prices(self, epic_id, interval, range):
        # Read mock file
        try:
            with open(self.mockPricesFilepath, 'r') as file:
                mock = json.load(file)
        except IOError:
            exit()
        return mock

@pytest.fixture
def config():
    """
    Returns a dict with config parameter for strategy and simpleMACD
    """
    # Read configuration file
    try:
        with open('config/config.json', 'r') as file:
            config = json.load(file)
            config['general']['use_av_api'] = False
    except IOError:
        exit()
    return config


def test_find_trade_signal(config):
    services = {
        'broker': MockBroker('test/test_data/mock_ig_market_info.json',
                                'test/test_data/mock_ig_historic_price.json'),
        'alpha_vantage': 'mock'
    }
    strategy = WeightedAvgPeak(config, services)
    tradeDir, limit, stop = strategy.find_trade_signal('MOCK')

    assert tradeDir is not None
    assert limit is None
    assert stop is None

    assert tradeDir == TradeDirection.NONE
