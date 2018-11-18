import os
import sys
import inspect
import pytest
import json
import pandas as pd

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

from scripts.Strategies.SimpleMACD import SimpleMACD
from scripts.Utils import TradeDirection

class MockBroker:
    """
    Mock broker interface class
    """
    def __init__(self, mockFilepath):
        self.mockFilepath = mockFilepath
        pass

    def get_market_info(self, epic_id):
        # Read mock file
        try:
            with open(self.mockFilepath, 'r') as file:
                mock = json.load(file)
        except IOError:
            exit()
        return mock

    def get_prices(self, epic_id, interval='DAY', range=26):
        # TODO
        return None

class MockAV:
    """
    Mock AlphaVantage interface class
    """
    def __init__(self, mockFilepath):
        self.mockFilepath = mockFilepath

    def macdext(self, marketId, interval):
        # Read mock file
        try:
            with open(self.mockFilepath, 'r') as file:
                mock = json.load(file)
                px = pd.DataFrame.from_dict(mock['Technical Analysis: MACDEXT'], orient='index', dtype=float)
        except IOError:
            exit()
        return px

@pytest.fixture
def config():
    """
    Returns a dict with config parameter for strategy and simpleMACD
    """
    # Read configuration file
    try:
        with open('config/config.json', 'r') as file:
            config = json.load(file)
    except IOError:
        exit()
    return config

def test_find_trade_signal(config):
    services = {
        'broker': MockBroker('test/test_data/mock_ig_market_info.json'),
        'alpha_vantage': MockAV('test/test_data/mock_macdext_buy.json')
    }
    strategy = SimpleMACD(config, services)
    tradeDir, limit, stop = strategy.find_trade_signal('MOCK')

    assert tradeDir is not None
    assert limit is not None
    assert stop is not None

    assert tradeDir.value == TradeDirection.BUY.value
