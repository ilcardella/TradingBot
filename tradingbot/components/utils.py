import functools
import threading
from enum import Enum
from typing import Any, Dict, List, Tuple, Union

import pandas


class TradeDirection(Enum):
    """
    Enumeration that represents the trade direction in the market: NONE means
    no action to take.
    """

    NONE = "NONE"
    BUY = "BUY"
    SELL = "SELL"


class Interval(Enum):
    """
    Time intervals for price and technical indicators requests
    """

    MINUTE_1 = "MINUTE_1"
    MINUTE_2 = "MINUTE_2"
    MINUTE_3 = "MINUTE_3"
    MINUTE_5 = "MINUTE_5"
    MINUTE_10 = "MINUTE_10"
    MINUTE_15 = "MINUTE_15"
    MINUTE_30 = "MINUTE_30"
    HOUR = "HOUR"
    HOUR_2 = "HOUR_2"
    HOUR_3 = "HOUR_3"
    HOUR_4 = "HOUR_4"
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"


class MarketClosedException(Exception):
    """Error to notify that the market is currently closed"""

    pass


class NotSafeToTradeException(Exception):
    """Error to notify that it is not safe to trade"""

    pass


# Mutex used for thread synchronisation
lock: threading.Lock = threading.Lock()


def synchronised(lock: threading.Lock) -> Any:
    """Thread synchronization decorator"""

    def wrapper(f: Any) -> Any:
        @functools.wraps(f)
        def inner_wrapper(*args: Any, **kw: Any) -> Any:
            with lock:
                return f(*args, **kw)

        return inner_wrapper

    return wrapper


class SynchSingleton(type):
    """Metaclass to implement the Singleton desing pattern"""

    _instances: Dict[Any, Any] = {}

    @synchronised(lock)
    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Singleton(type):
    """Metaclass to implement the Singleton desing pattern"""

    _instances: Dict[Any, Any] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Utils:
    """
    Utility class containing static methods to perform simple general actions
    """

    def __init__(self) -> None:
        pass

    @staticmethod
    def midpoint(p1: Union[int, float], p2: Union[int, float]) -> Union[int, float]:
        """Return the midpoint"""
        return (p1 + p2) / 2

    @staticmethod
    def percentage_of(
        percent: Union[int, float], whole: Union[int, float]
    ) -> Union[int, float]:
        """Return the value of the percentage on the whole"""
        return (percent * whole) / 100.0

    @staticmethod
    def percentage(
        part: Union[int, float], whole: Union[int, float]
    ) -> Union[int, float]:
        """Return the percentage value of the part on the whole"""
        return 100 * float(part) / float(whole)

    @staticmethod
    def is_between(time: str, time_range: Tuple[str, str]):
        """Return True if time is between the time_range. time must be a string.
        time_range must be a tuple (a,b) where a and b are strings in format 'HH:MM'"""
        if time_range[1] < time_range[0]:
            return time >= time_range[0] or time <= time_range[1]
        return time_range[0] <= time <= time_range[1]

    @staticmethod
    def humanize_time(secs: Union[int, float]) -> str:
        """Convert the given time (in seconds) into a readable format hh:mm:ss"""
        mins, secs = divmod(secs, 60)
        hours, mins = divmod(mins, 60)
        return "%02d:%02d:%02d" % (hours, mins, secs)

    @staticmethod
    def macd_df_from_list(price_list: List[float]) -> pandas.DataFrame:
        """Return a MACD pandas dataframe with columns "MACD", "Signal" and "Hist"""
        px = pandas.DataFrame({"close": price_list})
        px["26_ema"] = pandas.DataFrame.ewm(px["close"], span=26).mean()
        px["12_ema"] = pandas.DataFrame.ewm(px["close"], span=12).mean()
        px["MACD"] = px["12_ema"] - px["26_ema"]
        px["Signal"] = px["MACD"].rolling(9).mean()
        px["Hist"] = px["MACD"] - px["Signal"]
        return px
