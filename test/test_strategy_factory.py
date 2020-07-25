from pathlib import Path

import pytest

from tradingbot.Components.Configuration import Configuration
from tradingbot.Strategies.SimpleMACD import SimpleMACD
from tradingbot.Strategies.StrategyFactory import StrategyFactory
from tradingbot.Strategies.WeightedAvgPeak import WeightedAvgPeak


@pytest.fixture
def config():
    return Configuration.from_filepath(Path("test/test_data/config.json"))


@pytest.fixture
def broker():
    return "mock"


def test_make_strategy_fail(config, broker):
    sf = StrategyFactory(config, broker)
    with pytest.raises(ValueError):
        _ = sf.make_strategy("")

    with pytest.raises(ValueError):
        _ = sf.make_strategy("wrong")


def test_make_strategy(config, broker):
    sf = StrategyFactory(config, broker)
    strategy = sf.make_strategy("simple_macd")
    assert isinstance(strategy, SimpleMACD)

    strategy = sf.make_strategy("weighted_avg_peak")
    assert isinstance(strategy, WeightedAvgPeak)
