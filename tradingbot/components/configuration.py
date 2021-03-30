import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, MutableMapping, Optional, Union

import toml

DEFAULT_CONFIGURATION_PATH = Path.home() / ".TradingBot" / "config" / "trading_bot.toml"
CONFIGURATION_ROOT = "trading_bot_root"

# FIXME Property should be of type JSON byt it requires typing to accepts recursive types
Property = Any
ConfigDict = MutableMapping[str, Property]
CredentialDict = Dict[str, str]


class Configuration:
    config: ConfigDict

    def __init__(self, dictionary: ConfigDict) -> None:
        if not isinstance(dictionary, dict):
            raise ValueError("argument must be a dict")
        self.config = self._parse_raw_config(dictionary)
        logging.info("Configuration loaded")

    @staticmethod
    def from_filepath(filepath: Optional[Path]) -> "Configuration":
        filepath = filepath if filepath else DEFAULT_CONFIGURATION_PATH
        logging.debug("Loading configuration: {}".format(filepath))
        with filepath.open(mode="r") as f:
            return Configuration(toml.load(f))

    def _find_property(self, fields: List[str]) -> Union[ConfigDict, Property]:
        if CONFIGURATION_ROOT in fields:
            return self.config
        if type(fields) is not list or len(fields) < 1:
            raise ValueError("Can't find properties {} in configuration".format(fields))
        value = self.config[fields[0]]
        for f in fields[1:]:
            value = value[f]
        return value

    def _parse_raw_config(self, config_dict: ConfigDict) -> ConfigDict:
        config_copy = config_dict
        for key, value in config_copy.items():
            if type(value) is dict:
                config_dict[key] = self._parse_raw_config(value)
            elif type(value) is list:
                for i in range(len(value)):
                    config_dict[key][i] = (
                        self._replace_placeholders(config_dict[key][i])
                        if type(config_dict[key][i]) is str
                        else config_dict[key][i]
                    )
            elif type(value) is str:
                config_dict[key] = self._replace_placeholders(config_dict[key])
        return config_dict

    def _replace_placeholders(self, string: str) -> str:
        string = string.replace("{home}", str(Path.home()))
        string = string.replace(
            "{timestamp}",
            datetime.now().isoformat().replace(":", "_").replace(".", "_"),
        )
        return string

    def get_raw_config(self) -> ConfigDict:
        return self._find_property([CONFIGURATION_ROOT])

    def get_max_account_usable(self) -> Property:
        return self._find_property(["max_account_usable"])

    def get_time_zone(self) -> Property:
        return self._find_property(["time_zone"])

    def get_credentials_filepath(self) -> Property:
        return self._find_property(["credentials_filepath"])

    def get_credentials(self) -> CredentialDict:
        with Path(self.get_credentials_filepath()).open(mode="r") as f:
            return json.load(f)

    def get_spin_interval(self) -> Property:
        return self._find_property(["spin_interval"])

    def is_logging_enabled(self) -> Property:
        return self._find_property(["logging", "enable"])

    def get_log_filepath(self) -> Property:
        return self._find_property(["logging", "log_filepath"])

    def is_logging_debug_enabled(self) -> Property:
        return self._find_property(["logging", "debug"])

    def get_active_market_source(self) -> Property:
        return self._find_property(["market_source", "active"])

    def get_market_source_values(self) -> Property:
        return self._find_property(["market_source", "values"])

    def get_epic_ids_filepath(self) -> Property:
        return self._find_property(["market_source", "epic_id_list", "filepath"])

    def get_watchlist_name(self) -> Property:
        return self._find_property(["market_source", "watchlist", "name"])

    def get_active_stocks_interface(self) -> Property:
        return self._find_property(["stocks_interface", "active"])

    def get_stocks_interface_values(self) -> Property:
        return self._find_property(["stocks_interface", "values"])

    def get_ig_order_type(self) -> Property:
        return self._find_property(["stocks_interface", "ig_interface", "order_type"])

    def get_ig_order_size(self) -> Property:
        return self._find_property(["stocks_interface", "ig_interface", "order_size"])

    def get_ig_order_expiry(self) -> Property:
        return self._find_property(["stocks_interface", "ig_interface", "order_expiry"])

    def get_ig_order_currency(self) -> Property:
        return self._find_property(
            ["stocks_interface", "ig_interface", "order_currency"]
        )

    def get_ig_order_force_open(self) -> Property:
        return self._find_property(
            ["stocks_interface", "ig_interface", "order_force_open"]
        )

    def get_ig_use_g_stop(self) -> Property:
        return self._find_property(["stocks_interface", "ig_interface", "use_g_stop"])

    def get_ig_use_demo_account(self) -> Property:
        return self._find_property(
            ["stocks_interface", "ig_interface", "use_demo_account"]
        )

    def get_ig_controlled_risk(self):
        return self._find_property(
            ["stocks_interface", "ig_interface", "controlled_risk"]
        )

    def get_ig_api_timeout(self) -> Property:
        return self._find_property(["stocks_interface", "ig_interface", "api_timeout"])

    def is_paper_trading_enabled(self) -> Property:
        return self._find_property(["paper_trading"])

    def get_alphavantage_api_timeout(self) -> Property:
        return self._find_property(["stocks_interface", "alpha_vantage", "api_timeout"])

    def get_yfinance_api_timeout(self) -> Property:
        return self._find_property(["stocks_interface", "yfinance", "api_timeout"])

    def get_active_account_interface(self) -> Property:
        return self._find_property(["account_interface", "active"])

    def get_account_interface_values(self) -> Property:
        return self._find_property(["account_interface", "values"])

    def get_active_strategy(self) -> Property:
        return self._find_property(["strategies", "active"])

    def get_strategies_values(self) -> Property:
        return self._find_property(["strategies", "values"])
