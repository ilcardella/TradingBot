import datetime as dt
import time
import functools
import threading

from abc import abstractmethod

# Mutex used for thread synchronisation
lock = threading.Lock()


def synchronised(lock):
    """ Thread synchronization decorator """

    def wrapper(f):
        @functools.wraps(f)
        def inner_wrapper(*args, **kw):
            with lock:
                return f(*args, **kw)

        return inner_wrapper

    return wrapper


class Singleton(type):
    """Metaclass to implement the Singleton desing pattern"""

    _instances = {}

    @synchronised(lock)
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


# TODO ABC can't be used anymore as base class if we define the metaclass
class AbstractInterface(metaclass=Singleton):
    def __init__(self, config):
        self._config = config
        self._last_call_ts = dt.datetime.now()
        self.initialise()

    def _wait_before_call(self, timeout: float):
        """
        Wait between API calls to not overload the server
        """
        while (dt.datetime.now() - self._last_call_ts) <= dt.timedelta(seconds=timeout):
            time.sleep(0.5)
        self._last_call_ts = dt.datetime.now()


class AccountInterface(AbstractInterface):
    # This MUST not be overwritten. Use the "initialise()" to init a children interface
    def __init__(self, config):
        super().__init__(config)

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
        super()._wait_before_call(timeout)


class StocksInterface(AbstractInterface):
    # This MUST not be overwritten. Use the "initialise()" to init a children interface
    def __init__(self, config):
        super().__init__(config)

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
        super()._wait_before_call(timeout)
