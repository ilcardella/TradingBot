import os
import sys
import inspect
import pytest
import json

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, "{}/src".format(parentdir))

from Strategies.StrategyFactory import StrategyFactory
from Strategies.SimpleMACD import SimpleMACD
from Strategies.WeightedAvgPeak import WeightedAvgPeak


@pytest.fixture
def config():
    """
    Returns a dict with config parameter for strategy and simpleMACD
    """
    # Read configuration file
    try:
        with open("config/config.json", "r") as file:
            config = json.load(file)
    except IOError:
        exit()
    return config


@pytest.fixture
def broker():
    return "mock"


def test_make_strategy_fail(config, broker):
    sf = StrategyFactory(config, broker)
    strategy = sf.make_strategy("")
    assert strategy is None

    strategy = sf.make_strategy("wrong")
    assert strategy is None


def test_make_strategy(config, broker):
    sf = StrategyFactory(config, broker)
    strategy = sf.make_strategy("simple_macd")
    assert isinstance(strategy, SimpleMACD)

    strategy = sf.make_strategy("weighted_avg_peak")
    assert isinstance(strategy, WeightedAvgPeak)
