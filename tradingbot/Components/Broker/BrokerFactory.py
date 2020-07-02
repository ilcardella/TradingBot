from enum import Enum

from .IGInterface import IGInterface
from .AVInterface import AVInterface
from .YFinanceInterface import YFinanceInterface


class InterfaceNames(Enum):
    IG_INDEX = "ig_interface"
    ALPHA_VANTAGE = "alpha_vantage"
    YAHOO_FINANCE = "yfinance"


class BrokerFactory:
    def __init__(self, config):
        self.config = config

    def make(self, name):
        if name == InterfaceNames.IG_INDEX.value:
            return IGInterface(self.config)
        elif name == InterfaceNames.ALPHA_VANTAGE.value:
            return AVInterface(self.config)
        elif name == InterfaceNames.YAHOO_FINANCE.value:
            return YFinanceInterface(self.config)
        else:
            raise ValueError("Interface {} not supported".format(name))

    def make_stock_interface_from_config(self):
        return self.make(self.config.get_active_stocks_interface())

    def make_account_interface_from_config(self):
        return self.make(self.config.get_active_account_interface())
