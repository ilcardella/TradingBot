from pathlib import Path

import pytest

from tradingbot.components import Configuration
from tradingbot.strategies import SimpleMACD, StrategyFactory, VolumeProfile


@pytest.fixture
def config():
    return Configuration.from_filepath(Path("test/test_data/trading_bot.toml"))


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

    strategy = sf.make_strategy("volume_profile")
    assert isinstance(strategy, VolumeProfile)
