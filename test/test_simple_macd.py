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

@pytest.fixture
def strategy(config):
    """
    Initialise the strategy with mock services
    """
    services = {
        'ig_index': MockIG('test/test_data/mock_ig_market_info.json',
                                'test/test_data/mock_ig_historic_price.json'),
        'alpha_vantage': MockAV('test/test_data/mock_macdext_buy.json')
    }
    broker = MockBroker(config, services)
    return SimpleMACD(config, broker)

def test_find_trade_signal_buy(config):
    services = {
        'ig_index': MockIG('test/test_data/mock_ig_market_info.json',
                                'test/test_data/mock_ig_historic_price.json'),
        'alpha_vantage': MockAV('test/test_data/mock_macdext_buy.json') # BUY json
    }
    broker = MockBroker(config, services)
    strategy = SimpleMACD(config, broker)
    tradeDir, limit, stop = strategy.find_trade_signal('MOCK')

    assert tradeDir is not None
    assert limit is not None
    assert stop is not None

    assert tradeDir == TradeDirection.BUY

def test_find_trade_signal_sell(config):
    services = {
        'ig_index': MockIG('test/test_data/mock_ig_market_info.json',
                                'test/test_data/mock_ig_historic_price.json'),
        'alpha_vantage': MockAV('test/test_data/mock_macdext_sell.json') # SELL json
    }
    broker = MockBroker(config, services)
    strategy = SimpleMACD(config, broker)
    tradeDir, limit, stop = strategy.find_trade_signal('MOCK')

    assert tradeDir is not None
    assert limit is not None
    assert stop is not None

    assert tradeDir == TradeDirection.SELL

def test_find_trade_signal_hold(config):
    services = {
        'ig_index': MockIG('test/test_data/mock_ig_market_info.json',
                                'test/test_data/mock_ig_historic_price.json'),
        'alpha_vantage': MockAV('test/test_data/mock_macdext_hold.json') # HOLD json
    }
    broker = MockBroker(config, services)
    strategy = SimpleMACD(config, broker)
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

def test_generate_signals_from_dataframe(strategy):
    px = strategy.broker.macd_dataframe('mock', 'mock', 'mock')
    px = strategy.generate_signals_from_dataframe(px)

    assert 'positions' in px
    assert len(px) > 26
    # TODO add more checks

def test_get_trade_direction_from_signals(strategy):
    dataframe = strategy.broker.macd_dataframe('mock', 'mock', 'mock')
    dataframe = strategy.generate_signals_from_dataframe(dataframe)
    tradeDir = strategy.get_trade_direction_from_signals(dataframe)

    # BUY becasue the strategy fixture loads the buy test json
    assert tradeDir == TradeDirection.BUY
