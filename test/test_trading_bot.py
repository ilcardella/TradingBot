import os
import sys
import inspect
import pytest
import json

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, "{}/src".format(parentdir))

from TradingBot import TradingBot
from Components.TimeProvider import TimeProvider


def test_trading_bot_001():
    """
    TODO Define configuration of this test (list, watchlist, buy, sell,etc.)
    """
    # TODO
    # tb = TradingBot(TimeProvider())
    # tb2 = TradingBot()
    # assert tb
    # assert tb2
    assert True
