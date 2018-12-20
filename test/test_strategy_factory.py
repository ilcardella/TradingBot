import os
import sys
import inspect
import pytest
import json

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,'{}/src'.format(parentdir))

from Strategies.StrategyFactory import StrategyFactory
from Strategies.SimpleMACD import SimpleMACD
from Strategies.FAIG_iqr import FAIG_iqr


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


@pytest.fixture
def services():
    return {
        "broker": "mock",
        "alpha_vantage": "mock"
    }

def test_make_strategy_fail(config):
    sf = StrategyFactory(config)
    strategy = sf.make_strategy('')
    assert strategy is None

    strategy = sf.make_strategy('wrong')
    assert strategy is None

def test_make_strategy(config, services):
    sf = StrategyFactory(config)
    strategy = sf.make_strategy('simple_macd', config, services)
    assert isinstance(strategy, SimpleMACD)

    strategy = sf.make_strategy('faig', config, services)
    assert isinstance(strategy, FAIG_iqr)
