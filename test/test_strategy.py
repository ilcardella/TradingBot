import os
import sys
import inspect
import json
import pytest
import pandas as pd

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,'{}/scripts'.format(parentdir))

from Strategies.Strategy import Strategy
from Utils import TradeDirection

class MockBroker:
    """
    Mock broker interface class
    """
    def __init__(self, mockFilepath, mockPricesFilepath):
        self.mockFilepath = mockFilepath
        self.mockPricesFilepath = mockPricesFilepath

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

    def get_open_positions(self):
        # Read mock file
        try:
            with open('test/test_data/mock_ig_positions.json', 'r') as file:
                mock = json.load(file)
        except IOError:
            exit()
        return mock

    def get_account_used_perc(self):
        return 52

    def trade(self, epic_id, trade_direction, limit, stop):
        return True

    def confirm_order(self, dealRef):
        return True

    def close_position(self, position):
        return True


class MockStrategy(Strategy):
    """
    Mock strategy to test the parent class
    """
    def __init__(self, config, services, trade_dir, fail):
        super().__init__(config, services)
        self.positions = self.broker.get_open_positions()
        self.test_trade_dir = trade_dir
        self.test_fail = fail

    def read_configuration(self, config):
        pass

    def get_seconds_to_next_spin(self):
        return 1

    def find_trade_signal(self, epic_id):
        if self.test_fail:
            return TradeDirection.NONE, None, None
        if self.test_trade_dir == TradeDirection.BUY:
            return TradeDirection.BUY, 100, 300
        if self.test_trade_dir == TradeDirection.SELL:
            return TradeDirection.SELL, 100, 300
        if self.test_trade_dir == TradeDirection.NONE:
            return TradeDirection.NONE, 100, 300



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

def test_process_epic(config):
    services = {
        'broker': MockBroker('test/test_data/mock_ig_market_info.json',
                                'test/test_data/mock_ig_historic_price.json')
        ,
        'alpha_vantage': None
    }

    strategy = MockStrategy(config, services, TradeDirection.NONE, True)
    result = strategy.process_epic('mock')
    assert result == False

    strategy = MockStrategy(config, services, TradeDirection.NONE, False)
    result = strategy.process_epic('mock')
    assert result == False

    strategy = MockStrategy(config, services, TradeDirection.BUY, False)
    result = strategy.process_epic('mock')
    assert result

    strategy = MockStrategy(config, services, TradeDirection.SELL, False)
    result = strategy.process_epic('mock')
    assert result

def test_process_open_positions(config):
    services = {
        'broker': MockBroker('test/test_data/mock_ig_market_info.json',
                                'test/test_data/mock_ig_historic_price.json')
        ,
        'alpha_vantage': None
    }

    # Read mock file
    try:
        with open('test/test_data/mock_ig_positions.json', 'r') as file:
            mock = json.load(file)
    except IOError:
        exit()

    strategy = MockStrategy(config, services, TradeDirection.BUY, False)
    strategy.timeout = 0 # avoid waiting during test
    result = strategy.process_open_positions(mock)
    assert result

    result = strategy.process_open_positions(None)
    assert result == False

    result = strategy.process_open_positions({"positions":[]})
    assert result
