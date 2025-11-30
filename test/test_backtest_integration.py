from pathlib import Path
from unittest.mock import patch

import pytest
from common.MockRequests import (
    ig_request_login,
    ig_request_set_account,
    ig_request_watchlist,
)

from tradingbot import TradingBot
from tradingbot.components import TimeProvider


class MockTimeProvider(TimeProvider):
    def __init__(self):
        pass

    def is_market_open(self, timezone):
        return True

    def wait_for(self, time_amount_type, amount=-1):
        pass


@pytest.fixture
def mock_ig_login(requests_mock):
    ig_request_login(requests_mock)
    ig_request_set_account(requests_mock)
    ig_request_watchlist(requests_mock)


@pytest.fixture
def sample_csv(tmp_path):
    d = tmp_path / "data"
    d.mkdir()
    p = d / "test_data.csv"
    p.write_text("""Gmt time,Open,High,Low,Close,Volume
2024-01-01 00:00:00,100.0,105.0,95.0,102.0,1000
2024-01-02 00:00:00,102.0,107.0,100.0,105.0,1200
2024-01-03 00:00:00,105.0,110.0,103.0,108.0,1500
2024-01-04 00:00:00,108.0,109.0,101.0,103.0,1100
2024-01-05 00:00:00,103.0,105.0,99.0,100.0,900
""")
    return str(p)


@patch("tradingbot.trading_bot.Backtester")
def test_backtest_integration_mock(mock_backtester_cls, sample_csv, mock_ig_login):
    """
    Test that TradingBot.backtest initializes Backtester and calls start/print_results
    """
    # Setup
    config_path = Path("test/test_data/trading_bot.toml")
    bot = TradingBot(MockTimeProvider(), config_filepath=config_path)

    # Mock the backtester instance
    mock_bt_instance = mock_backtester_cls.return_value

    # Execute
    bot.backtest(
        csv_path=sample_csv, cash=5000, commission=0.001, plot_filename="plot.html"
    )

    # Verify
    mock_backtester_cls.assert_called_once_with(bot.strategy)
    mock_bt_instance.start.assert_called_once_with(
        csv_path=sample_csv, cash=5000, commission=0.001
    )
    mock_bt_instance.print_results.assert_called_once()
    mock_bt_instance.plot_results.assert_called_once_with(filename="plot.html")


def test_backtest_integration_real(sample_csv, mock_ig_login):
    """
    Test that TradingBot.backtest runs with real Backtester (integration test)
    """
    # Setup
    config_path = Path("test/test_data/trading_bot.toml")
    bot = TradingBot(MockTimeProvider(), config_filepath=config_path)

    # Execute - should not raise exception
    try:
        bot.backtest(csv_path=sample_csv, cash=10000, commission=0.0)
    except Exception as e:
        pytest.fail(f"Backtest failed with exception: {e}")
