import os
import sys
import inspect
import pytest
import json

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,'{}/src'.format(parentdir))

from TradingBot import TradingBot

def test_trading_bot_001():
    """
    TODO Define configuration of this test (list, watchlist, buy, sell,etc.)
    """
    # TODO
    # Create MockIGInterface
    # Create MockAlphaVantageInterface
    # Setup mock IG ifc to return data as per test case configuration
    # Create TradingBot()
    # Call start()
    # Assert from the mock ig interface the trades where as expected
    assert True
