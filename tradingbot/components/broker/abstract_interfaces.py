import datetime as dt
import time
from abc import abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from ...interfaces import Market, MarketHistory, MarketMACD, Position
from .. import Configuration, Interval, SynchSingleton, TradeDirection

AccountBalances = Tuple[Optional[float], Optional[float]]


# TODO ABC can't be used anymore as base class if we define the metaclass
class AbstractInterface(metaclass=SynchSingleton):
    def __init__(self, config: Configuration) -> None:
        self._config = config
        self._last_call_ts = dt.datetime.now()
        self.initialise()

    def _wait_before_call(self, timeout: float) -> None:
        """
        Wait between API calls to not overload the server
        """
        while (dt.datetime.now() - self._last_call_ts) <= dt.timedelta(seconds=timeout):
            time.sleep(0.5)
        self._last_call_ts = dt.datetime.now()

    @abstractmethod
    def initialise(self) -> None:
        pass


class AccountInterface(AbstractInterface):
    # This MUST not be overwritten. Use the "initialise()" to init a children interface
    def __init__(self, config: Configuration) -> None:
        super().__init__(config)

    @abstractmethod
    def authenticate(self) -> bool:
        pass

    @abstractmethod
    def set_default_account(self, account_id: str) -> bool:
        pass

    @abstractmethod
    def get_account_balances(self) -> AccountBalances:
        pass

    @abstractmethod
    def get_open_positions(self) -> List[Position]:
        pass

    @abstractmethod
    def get_positions_map(self) -> Dict[str, int]:
        pass

    @abstractmethod
    def get_market_info(self, market_ticker: str) -> Market:
        pass

    @abstractmethod
    def search_market(self, search_string: str) -> List[Market]:
        pass

    @abstractmethod
    def trade(
        self, ticker: str, direction: TradeDirection, limit: float, stop: float
    ) -> bool:
        pass

    @abstractmethod
    def close_position(self, position: Position) -> bool:
        pass

    @abstractmethod
    def close_all_positions(self) -> bool:
        pass

    @abstractmethod
    def get_account_used_perc(self) -> Optional[float]:
        pass

    @abstractmethod
    def get_markets_from_watchlist(self, watchlist_id: str) -> List[Market]:
        pass

    @abstractmethod
    def navigate_market_node(self, node_id: str) -> Dict[str, Any]:
        pass


class StocksInterface(AbstractInterface):
    # This MUST not be overwritten. Use the "initialise()" to init a children interface
    def __init__(self, config: Configuration) -> None:
        super().__init__(config)

    @abstractmethod
    def get_prices(
        self, market: Market, interval: Interval, data_range: int
    ) -> MarketHistory:
        pass

    @abstractmethod
    def get_macd(
        self, market: Market, interval: Interval, data_range: int
    ) -> MarketMACD:
        pass
