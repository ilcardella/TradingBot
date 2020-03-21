import os
import sys
import inspect
from abc import ABC, abstractmethod
import datetime as dt

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)


class AccountInterface(ABC):
    # This MUST not be overwritten. Use the "initialise()" to init a children interface
    def __init__(self, config):
        self._config = config
        self._last_call_ts = dt.datetime.now()
        self.initialise()

    @abstractmethod
    def initialise(self):
        pass

    @abstractmethod
    def authenticate(self):
        pass

    @abstractmethod
    def set_default_account(self, account_id):
        pass

    @abstractmethod
    def get_account_balances(self):
        pass

    @abstractmethod
    def get_open_positions(self):
        pass

    @abstractmethod
    def get_positions_map(self):
        pass

    @abstractmethod
    def get_market_info(self, market_ticker):
        pass

    @abstractmethod
    def search_market(self, search_string):
        pass

    @abstractmethod
    def trade(self, ticker, direction, limit, stop):
        pass

    @abstractmethod
    def close_position(self, position):
        pass

    @abstractmethod
    def close_all_positions(self):
        pass

    @abstractmethod
    def get_account_used_perc(self):
        pass

    @abstractmethod
    def get_markets_from_watchlist(self, watchlist_id):
        pass

    # No need to override this
    def _wait_before_call(self, timeout: float):
        """
        Wait between API calls to not overload the server
        """
        while (dt.datetime.now() - self._last_call_ts) <= dt.timedelta(seconds=timeout):
            time.sleep(0.5)
        self._last_call_ts = dt.datetime.now()


class StocksInterface(ABC):
    # This MUST not be overwritten. Use the "initialise()" to init a children interface
    def __init__(self, config):
        self._config = config
        self._last_call_ts = dt.datetime.now()
        self.initialise()

    @abstractmethod
    def initialise(self):
        pass

    @abstractmethod
    def get_prices(self, market, interval, data_range):
        pass

    @abstractmethod
    def get_macd(self, market, interval, data_range):
        pass

    # No need to override this
    def _wait_before_call(self, timeout: float):
        """
        Wait between API calls to not overload the server
        """
        while (dt.datetime.now() - self._last_call_ts) <= dt.timedelta(seconds=timeout):
            time.sleep(0.5)
        self._last_call_ts = dt.datetime.now()
