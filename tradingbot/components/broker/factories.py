from enum import Enum
from typing import TypeVar, Union

from .. import Configuration
from . import (
    AccountInterface,
    AVInterface,
    IGInterface,
    StocksInterface,
    YFinanceInterface,
)

AccountInterfaceImpl = TypeVar("AccountInterfaceImpl", bound=AccountInterface)
StocksInterfaceImpl = TypeVar("StocksInterfaceImpl", bound=StocksInterface)
BrokerInterfaces = Union[AccountInterfaceImpl, StocksInterfaceImpl]


class InterfaceNames(Enum):
    IG_INDEX = "ig_interface"
    ALPHA_VANTAGE = "alpha_vantage"
    YAHOO_FINANCE = "yfinance"


class BrokerFactory:
    config: Configuration

    def __init__(self, config: Configuration) -> None:
        self.config = config

    def make(self, name: str) -> BrokerInterfaces:
        if name == InterfaceNames.IG_INDEX.value:
            return IGInterface(self.config)
        elif name == InterfaceNames.ALPHA_VANTAGE.value:
            return AVInterface(self.config)
        elif name == InterfaceNames.YAHOO_FINANCE.value:
            return YFinanceInterface(self.config)
        else:
            raise ValueError("Interface {} not supported".format(name))

    def make_stock_interface_from_config(
        self,
    ) -> BrokerInterfaces:
        return self.make(self.config.get_active_stocks_interface())

    def make_account_interface_from_config(
        self,
    ) -> BrokerInterfaces:
        return self.make(self.config.get_active_account_interface())
