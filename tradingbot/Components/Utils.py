import functools
import threading
from enum import Enum

import pandas as pd


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


class Singleton(type):
    """Metaclass to implement the Singleton desing pattern"""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


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


class SynchSingleton(type):
    """Metaclass to implement the Singleton desing pattern"""

    _instances = {}

    @synchronised(lock)
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Utils:
    """
    Utility class containing static methods to perform simple general actions
    """

    def __init__(self):
        pass

    @staticmethod
    def midpoint(p1, p2):
        """Return the midpoint"""
        return (p1 + p2) / 2

    @staticmethod
    def percentage_of(percent, whole):
        """Return the value of the percentage on the whole"""
        return (percent * whole) / 100.0

    @staticmethod
    def percentage(part, whole):
        """Return the percentage value of the part on the whole"""
        return 100 * float(part) / float(whole)

    @staticmethod
    def is_between(time, time_range):
        """Return True if time is between the time_range. time must be a string.
        time_range must be a tuple (a,b) where a and b are strings in format 'HH:MM'"""
        if time_range[1] < time_range[0]:
            return time >= time_range[0] or time <= time_range[1]
        return time_range[0] <= time <= time_range[1]

    @staticmethod
    def humanize_time(secs):
        """Convert the given time (in seconds) into a readable format hh:mm:ss"""
        mins, secs = divmod(secs, 60)
        hours, mins = divmod(mins, 60)
        return "%02d:%02d:%02d" % (hours, mins, secs)

    @staticmethod
    def macd_df_from_list(price_list):
        """Return a MACD pandas dataframe with columns "MACD", "Signal" and "Hist"""
        px = pd.DataFrame({"close": price_list})
        px["26_ema"] = pd.DataFrame.ewm(px["close"], span=26).mean()
        px["12_ema"] = pd.DataFrame.ewm(px["close"], span=12).mean()
        px["MACD"] = px["12_ema"] - px["26_ema"]
        px["Signal"] = px["MACD"].rolling(9).mean()
        px["Hist"] = px["MACD"] - px["Signal"]
        return px
