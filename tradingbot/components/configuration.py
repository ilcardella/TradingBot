import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, MutableMapping, Optional

import toml

from .config_model import TradingBotConfig

DEFAULT_CONFIGURATION_PATH = Path.home() / ".TradingBot" / "config" / "trading_bot.toml"
CONFIGURATION_ROOT = "trading_bot_root"

# FIXME Property should be of type JSON byt it requires typing to accepts recursive types
Property = Any
ConfigDict = MutableMapping[str, Property]
CredentialDict = Dict[str, str]


class Configuration:
    config: TradingBotConfig
    _raw_config: ConfigDict

    def __init__(self, dictionary: ConfigDict) -> None:
        if not isinstance(dictionary, dict):
            raise ValueError("argument must be a dict")
        # Process placeholders before validation
        processed_config = self._parse_raw_config(dictionary)
        self._raw_config = processed_config
        self.config = TradingBotConfig(**processed_config)
        logging.info("Configuration loaded")

    @staticmethod
    def from_filepath(filepath: Optional[Path]) -> "Configuration":
        filepath = filepath if filepath else DEFAULT_CONFIGURATION_PATH
        logging.debug(f"Loading configuration: {filepath}")
        with filepath.open(mode="r") as f:
            return Configuration(toml.load(f))

    def _parse_raw_config(self, config_dict: ConfigDict) -> ConfigDict:
        config_copy = dict(config_dict)
        for key, value in config_copy.items():
            if isinstance(value, dict):
                config_copy[key] = self._parse_raw_config(value)
            elif isinstance(value, list):
                new_list = []
                for item in value:
                    if isinstance(item, str):
                        new_list.append(self._replace_placeholders(item))
                    else:
                        new_list.append(item)
                config_copy[key] = new_list
            elif isinstance(value, str):
                config_copy[key] = self._replace_placeholders(value)
        return config_copy

    def _replace_placeholders(self, string: str) -> str:
        string = string.replace("{home}", str(Path.home()))
        string = string.replace(
            "{timestamp}",
            datetime.now().isoformat().replace(":", "_").replace(".", "_"),
        )
        return string

    def get_raw_config(self) -> ConfigDict:
        return self._raw_config

    def get_max_account_usable(self) -> float:
        return self.config.max_account_usable

    def get_time_zone(self) -> str:
        return self.config.time_zone

    def get_credentials_filepath(self) -> str:
        return self.config.credentials_filepath

    def get_credentials(self) -> CredentialDict:
        with Path(self.get_credentials_filepath()).open(mode="r") as f:
            return json.load(f)

    def get_spin_interval(self) -> int:
        return self.config.spin_interval

    def is_logging_enabled(self) -> bool:
        return self.config.logging.enable

    def get_log_filepath(self) -> str:
        return self.config.logging.log_filepath

    def is_logging_debug_enabled(self) -> bool:
        return self.config.logging.debug

    def get_active_market_source(self) -> str:
        return self.config.market_source.active

    def get_market_source_values(self) -> List[str]:
        return self.config.market_source.values

    def get_epic_ids_filepath(self) -> str:
        if self.config.market_source.epic_id_list:
            return self.config.market_source.epic_id_list.filepath
        raise ValueError("epic_id_list configuration missing")

    def get_watchlist_name(self) -> str:
        if self.config.market_source.watchlist:
            return self.config.market_source.watchlist.name
        raise ValueError("watchlist configuration missing")

    def get_active_stocks_interface(self) -> str:
        return self.config.stocks_interface.active

    def get_stocks_interface_values(self) -> List[str]:
        return self.config.stocks_interface.values

    def get_ig_order_type(self) -> str:
        if self.config.stocks_interface.ig_interface:
            return self.config.stocks_interface.ig_interface.order_type
        raise ValueError("IG interface configuration missing")

    def get_ig_order_size(self) -> float:
        if self.config.stocks_interface.ig_interface:
            return self.config.stocks_interface.ig_interface.order_size
        raise ValueError("IG interface configuration missing")

    def get_ig_order_expiry(self) -> str:
        if self.config.stocks_interface.ig_interface:
            return self.config.stocks_interface.ig_interface.order_expiry
        raise ValueError("IG interface configuration missing")

    def get_ig_order_currency(self) -> str:
        if self.config.stocks_interface.ig_interface:
            return self.config.stocks_interface.ig_interface.order_currency
        raise ValueError("IG interface configuration missing")

    def get_ig_order_force_open(self) -> bool:
        if self.config.stocks_interface.ig_interface:
            return self.config.stocks_interface.ig_interface.order_force_open
        raise ValueError("IG interface configuration missing")

    def get_ig_use_g_stop(self) -> bool:
        if self.config.stocks_interface.ig_interface:
            return self.config.stocks_interface.ig_interface.use_g_stop
        raise ValueError("IG interface configuration missing")

    def get_ig_use_demo_account(self) -> bool:
        if self.config.stocks_interface.ig_interface:
            return self.config.stocks_interface.ig_interface.use_demo_account
        raise ValueError("IG interface configuration missing")

    def get_ig_controlled_risk(self) -> bool:
        if self.config.stocks_interface.ig_interface:
            return self.config.stocks_interface.ig_interface.controlled_risk
        raise ValueError("IG interface configuration missing")

    def get_ig_api_timeout(self) -> float:
        if self.config.stocks_interface.ig_interface:
            return self.config.stocks_interface.ig_interface.api_timeout
        raise ValueError("IG interface configuration missing")

    def is_paper_trading_enabled(self) -> bool:
        return self.config.paper_trading

    def get_alphavantage_api_timeout(self) -> float:
        if self.config.stocks_interface.alpha_vantage:
            return self.config.stocks_interface.alpha_vantage.api_timeout
        raise ValueError("Alpha Vantage configuration missing")

    def get_yfinance_api_timeout(self) -> float:
        if self.config.stocks_interface.yfinance:
            return self.config.stocks_interface.yfinance.api_timeout
        raise ValueError("YFinance configuration missing")

    def get_active_account_interface(self) -> str:
        return self.config.account_interface.active

    def get_account_interface_values(self) -> List[str]:
        return self.config.account_interface.values

    def get_active_strategy(self) -> str:
        return self.config.strategies.active

    def get_strategies_values(self) -> List[str]:
        return self.config.strategies.values
