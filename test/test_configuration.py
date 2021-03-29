from pathlib import Path

import pytest

from tradingbot.components import Configuration


def test_init():
    config = Configuration({})
    assert config is not None
    with pytest.raises(ValueError):
        config = Configuration([1])
    with pytest.raises(ValueError):
        config = Configuration((1, 1))
    with pytest.raises(ValueError):
        config = Configuration("mock")
    with pytest.raises(ValueError):
        config = Configuration(1.0)
    with pytest.raises(ValueError):
        config = Configuration(1)


def test_from_filepath():
    with pytest.raises(FileNotFoundError):
        config = Configuration.from_filepath(Path("wrong/path"))
    config = Configuration.from_filepath(Path("test/test_data/trading_bot.toml"))
    assert config is not None


def test_get_raw_config():
    mock_dict = {
        "key_string": "string1",
        "key_list": ["string1", "string2"],
        "key_dict": {
            "subkey1": "subvalue1",
            "subkey2": [1, 2, 3],
            "subkey3": {"subsubkey1": 1.0, "subsubkey2": "subsubvalue"},
        },
    }
    config = Configuration(mock_dict)
    assert config is not None
    raw = config.get_raw_config()
    assert raw == mock_dict


def test_value_getters():
    config = Configuration.from_filepath(Path("test/test_data/trading_bot.toml"))
    assert config is not None
    assert config.get_max_account_usable() == 90
    assert config.get_time_zone() == "Europe/London"
    assert config.get_credentials_filepath() == "test/test_data/credentials.json"
    credentials = config.get_credentials()
    assert type(credentials) is dict
    assert "username" in credentials
    assert credentials["username"] == "username"
    assert "password" in credentials
    assert credentials["password"] == "password"
    assert "api_key" in credentials
    assert credentials["api_key"] == "key"
    assert "account_id" in credentials
    assert credentials["account_id"] == "abcd"
    assert "av_api_key" in credentials
    assert credentials["av_api_key"] == "qwerty"
    assert config.get_spin_interval() == 3600
    assert config.is_logging_enabled()
    assert "/tmp/trading_bot" in config.get_log_filepath()
    assert "{timestamp}" not in config.get_log_filepath()
    assert not config.is_logging_debug_enabled()
    assert config.get_active_market_source() == "watchlist"
    assert config.get_market_source_values() == ["list", "api", "watchlist"]
    assert config.get_epic_ids_filepath() == "test/test_data/epic_ids.txt"
    assert config.get_watchlist_name() == "trading_bot"
    assert config.get_active_stocks_interface() == "ig_interface"
    assert config.get_stocks_interface_values() == [
        "yfinance",
        "alpha_vantage",
        "ig_interface",
    ]
    assert config.get_ig_order_type() == "MARKET"
    assert config.get_ig_order_size() == 1
    assert config.get_ig_order_expiry() == "DFB"
    assert config.get_ig_order_currency() == "GBP"
    assert config.get_ig_order_force_open()
    assert not config.get_ig_use_g_stop()
    assert config.get_ig_use_demo_account()
    assert not config.get_ig_controlled_risk()
    assert config.get_ig_api_timeout() == 0
    assert not config.is_paper_trading_enabled()
    assert config.get_alphavantage_api_timeout() == 12
    assert config.get_yfinance_api_timeout() == 0.5
    assert config.get_active_account_interface() == "ig_interface"
    assert config.get_account_interface_values() == ["ig_interface"]
    assert config.get_active_strategy() == "simple_macd"
    assert config.get_strategies_values() == [
        "simple_macd",
        "weighted_avg_peak",
        "simple_boll_bands",
    ]


def test_replace_placeholders():
    mock_dict = {
        "key_string": "string1",
        "key_list": ["string1", "string2"],
        "key_dict": {
            "subkey1": "{home}/path/file",
            "subkey2": [1, 2, 3],
            "subkey3": {"subsubkey1": 1.0, "subsubkey2": "file_{timestamp}"},
        },
    }
    config = Configuration(mock_dict)
    assert config is not None
    raw = config.get_raw_config()
    assert "{home}" not in raw["key_dict"]["subkey1"]
    assert "{timestamp}" not in raw["key_dict"]["subkey3"]["subsubkey2"]
