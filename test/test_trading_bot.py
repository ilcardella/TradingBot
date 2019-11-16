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
from common.MockRequests import ig_request_login, ig_request_set_account


def test_trading_bot_init(requests_mock):
    """
    Test init
    """
    ig_request_login(requests_mock)
    ig_request_set_account(requests_mock)
    config = "test/test_data/config.json"
    tb = TradingBot(TimeProvider(), config_filepath=config)
    tb2 = TradingBot(config_filepath=config)
    assert tb
    assert tb2
