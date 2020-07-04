import json
import logging

DEFAULT_CONFIGURATION_PATH = "/opt/TradingBot/config/config.json"
CONFIGURATION_ROOT = "trading_mate_root"


class Configuration:
    def __init__(self, dictionary):
        if not isinstance(dictionary, dict):
            raise ValueError("argument must be a dict")
        self.config = dictionary
        logging.info("Configuration loaded")

    @staticmethod
    def from_filepath(filepath):
        filepath = filepath if filepath else DEFAULT_CONFIGURATION_PATH
        logging.debug("Loading configuration from: {}".format(filepath))
        with open(filepath, "r") as f:
            return Configuration(json.load(f))

    def _find_property(self, fields):
        if CONFIGURATION_ROOT in fields:
            return self.config
        if not isinstance(fields, list) or len(fields) < 1:
            raise ValueError("Can't find properties {} in configuration".format(fields))
        value = self.config[fields[0]]
        for f in fields[1:]:
            value = value[f]
        return value

    def get_raw_config(self):
        return self._find_property(CONFIGURATION_ROOT)

    def get_max_account_usable(self):
        return self._find_property(["max_account_usable"])

    def get_time_zone(self):
        return self._find_property(["time_zone"])

    def get_credentials_filepath(self):
        return self._find_property(["credentials_filepath"])

    def get_credentials(self):
        filepath = self.get_credentials_filepath()
        with open(filepath, "r") as f:
            return json.load(f)

    def get_spin_interval(self):
        return self._find_property(["spin_interval"])

    def is_logging_enabled(self):
        return self._find_property(["logging", "enable"])

    def get_log_filepath(self):
        return self._find_property(["logging", "log_filepath"])

    def is_logging_debug_enabled(self):
        return self._find_property(["logging", "debug"])

    def get_active_market_source(self):
        return self._find_property(["market_source", "active"])

    def get_market_source_values(self):
        return self._find_property(["market_source", "values"])

    def get_epic_ids_filepath(self):
        return self._find_property(["market_source", "epic_ids_filepath"])

    def get_watchlist_name(self):
        return self._find_property(["market_source", "watchlist_name"])

    def get_active_stocks_interface(self):
        return self._find_property(["stocks_interface", "active"])

    def get_stocks_interface_values(self):
        return self._find_property(["stocks_interface", "values"])

    def get_ig_order_type(self):
        return self._find_property(["stocks_interface", "ig_interface", "order_type"])

    def get_ig_order_size(self):
        return self._find_property(["stocks_interface", "ig_interface", "order_size"])

    def get_ig_order_expiry(self):
        return self._find_property(["stocks_interface", "ig_interface", "order_expiry"])

    def get_ig_order_currency(self):
        return self._find_property(
            ["stocks_interface", "ig_interface", "order_currency"]
        )

    def get_ig_order_force_open(self):
        return self._find_property(
            ["stocks_interface", "ig_interface", "order_force_open"]
        )

    def get_ig_use_g_stop(self):
        return self._find_property(["stocks_interface", "ig_interface", "use_g_stop"])

    def get_ig_use_demo_account(self):
        return self._find_property(
            ["stocks_interface", "ig_interface", "use_demo_account"]
        )

    def get_ig_controlled_risk(self):
        return self._find_property(
            ["stocks_interface", "ig_interface", "controlled_risk"]
        )

    def get_ig_paper_trading(self):
        return self._find_property(
            ["stocks_interface", "ig_interface", "paper_trading"]
        )

    def get_alphavantage_api_timeout(self):
        return self._find_property(["stocks_interface", "alpha_vantage", "api_timeout"])

    def get_yfinance_api_timeout(self):
        return self._find_property(["stocks_interface", "yfinance", "api_timeout"])

    def get_active_account_interface(self):
        return self._find_property(["account_interface", "active"])

    def get_account_interface_values(self):
        return self._find_property(["account_interface", "values"])

    def get_active_strategy(self):
        return self._find_property(["strategies", "active"])

    def get_strategies_values(self):
        return self._find_property(["strategies", "values"])
