import os
import sys
import inspect
import pytest
import json
import pandas as pd

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,'{}/src'.format(parentdir))

from Strategies.SimpleMACD import SimpleMACD
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
            config['general']['use_av_api'] = True
    except IOError:
        exit()
    return config

@pytest.fixture
def strategy(config):
    """
    Initialise the strategy with mock services
    """
    services = {
        'broker': MockBroker('test/test_data/mock_ig_market_info.json',
                                'test/test_data/mock_ig_historic_price.json'),
        'alpha_vantage': MockAV('test/test_data/mock_macdext_buy.json')
    }
    return SimpleMACD(config, services)

def test_find_trade_signal_buy(config):
    services = {
        'broker': MockBroker('test/test_data/mock_ig_market_info.json',
                                'test/test_data/mock_ig_historic_price.json'),
        'alpha_vantage': MockAV('test/test_data/mock_macdext_buy.json') # BUY json
    }
    strategy = SimpleMACD(config, services)
    tradeDir, limit, stop = strategy.find_trade_signal('MOCK')

    assert tradeDir is not None
    assert limit is not None
    assert stop is not None

    assert tradeDir == TradeDirection.BUY

def test_find_trade_signal_sell(config):
    services = {
        'broker': MockBroker('test/test_data/mock_ig_market_info.json',
                                'test/test_data/mock_ig_historic_price.json'),
        'alpha_vantage': MockAV('test/test_data/mock_macdext_sell.json') # SELL json
    }
    strategy = SimpleMACD(config, services)
    tradeDir, limit, stop = strategy.find_trade_signal('MOCK')

    assert tradeDir is not None
    assert limit is not None
    assert stop is not None

    assert tradeDir == TradeDirection.SELL

def test_find_trade_signal_hold(config):
    services = {
        'broker': MockBroker('test/test_data/mock_ig_market_info.json',
                                'test/test_data/mock_ig_historic_price.json'),
        'alpha_vantage': MockAV('test/test_data/mock_macdext_hold.json') # HOLD json
    }
    strategy = SimpleMACD(config, services)
    tradeDir, limit, stop = strategy.find_trade_signal('MOCK')

    assert tradeDir is not None
    assert limit is None
    assert stop is None

    assert tradeDir == TradeDirection.NONE

def test_find_trade_signal_exception(config):
    #TODO provide wrong data and assert exception thrown
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

def test_get_market_snapshot(strategy):
    marketId, current_bid, current_offer, limit_perc, stop_perc = strategy.get_market_snapshot('mock')

    # TODO MockBroker should save a self instance of the json read from file
    # These asserts should refer to the values in that json object rather than being hardcoded
    assert marketId == 'GSK-UK'
    assert current_bid == 1562.0
    assert current_offer == 1565.8
    assert limit_perc == strategy.limit_p
    assert stop_perc == strategy.stop_p

def test_get_market_snapshot_invalid(strategy):
    # TODO add exception test cases, wrong id, null bid, null offer, etc.
    assert True

def test_compute_macd_from_timeseries(strategy):
    prices = strategy.broker.get_prices('mock', 'mock', 0)
    px = strategy.compute_macd_from_timeseries(prices)

    assert len(px) > 26 # 26 is the length of datapoint used
    assert 'MACD' in px.columns
    assert 'MACD_Signal' in px.columns
    assert 'MACD_Hist' in px.columns
    # TODO add more checks

def test_get_dataframe_from_historic_prices(strategy):
    px = strategy.get_dataframe_from_historic_prices('mock', 'mock')

    assert len(px) > 26 # 26 is the length of datapoint used
    assert 'MACD' in px.columns
    assert 'MACD_Signal' in px.columns
    assert 'MACD_Hist' in px.columns
    # TODO add more checks

def test_generate_signals_from_dataframe(strategy):
    dataframe = strategy.get_dataframe_from_historic_prices('mock', 'mock')
    px = strategy.generate_signals_from_dataframe(dataframe)

    assert 'positions' in px
    assert len(px) > 26
    # TODO add more checks

def test_get_trade_direction_from_signals(strategy):
    dataframe = strategy.get_dataframe_from_historic_prices('mock', 'mock')
    dataframe = strategy.generate_signals_from_dataframe(dataframe)
    tradeDir = strategy.get_trade_direction_from_signals(dataframe)

    # BUY becasue the strategy fixture loads the buy test json
    assert tradeDir == TradeDirection.BUY
