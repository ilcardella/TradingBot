from enum import Enum
from typing import Union

from ..Configuration import Configuration
from .AVInterface import AVInterface
from .IGInterface import IGInterface
from .YFinanceInterface import YFinanceInterface

InterfaceTypes = Union[IGInterface, AVInterface, YFinanceInterface]


class InterfaceNames(Enum):
    IG_INDEX = "ig_interface"
    ALPHA_VANTAGE = "alpha_vantage"
    YAHOO_FINANCE = "yfinance"


class BrokerFactory:
    config: Configuration

    def __init__(self, config: Configuration) -> None:
        self.config = config

    def make(self, name: str) -> InterfaceTypes:
        if name == InterfaceNames.IG_INDEX.value:
            return IGInterface(self.config)
        elif name == InterfaceNames.ALPHA_VANTAGE.value:
            return AVInterface(self.config)
        elif name == InterfaceNames.YAHOO_FINANCE.value:
            return YFinanceInterface(self.config)
        else:
            raise ValueError("Interface {} not supported".format(name))

    def make_stock_interface_from_config(self) -> InterfaceTypes:
        return self.make(self.config.get_active_stocks_interface())

    def make_account_interface_from_config(self) -> InterfaceTypes:
        return self.make(self.config.get_active_account_interface())
