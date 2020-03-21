import logging
from enum import Enum
import os
import sys
import inspect
import yfinance as yf

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from Components.Utils import Interval
from Interfaces.MarketHistory import MarketHistory
from Interfaces.MarketMACD import MarketMACD
from .AbstractInterfaces import StocksInterface


class YFInterval(Enum):
    MIN_1 = "1m"
    MIN_2 = "2m"
    MIN_5 = "5m"
    MIN_15 = "15"
    MIN_30 = "30m"
    MIN_60 = "60m"
    MIN_90 = "90m"
    HOUR = "1h"
    DAY_1 = "1d"
    DAY_5 = "5d"
    WEEK_1 = "1wk"
    MONTH_1 = "1mo"
    MONTH_3 = "3mo"


class YFinanceInterface(StocksInterface):
    def initialise(self):
        logging.info("YFinanceInterface initialised.")

    def get_prices(self, market, interval, data_range):
        self._wait_before_call(self._config.get_yfinance_api_timeout())

        ticker = yf.Ticker(self._format_market_id(market.id))
        data = ticker.history(
            period="max", interval=self._to_yf_interval(interval).value
        )

        history = MarketHistory(
            market,
            data.index,
            data["High"].values,
            data["Low"].values,
            data["Close"].values,
            data["Volume"].values,
        )
        return history

    def get_macd(self, market, interval, data_range):
        self._wait_before_call(self._config.get_yfinance_api_timeout())
        # TODO
        raise NotImplementedError()

    def _format_market_id(self, market_id) -> str:
        market_id = market_id.replace("-UK", "")
        return "{}.L".format(market_id)

    def _to_yf_interval(self, interval: Interval) -> YFInterval:
        if interval == Interval.MINUTE_1:
            return YFInterval.MIN_1
        elif interval == Interval.MINUTE_2:
            return YFInterval.MIN_2
        elif interval == Interval.MINUTE_3:
            raise ValueError("Interval.MINUTE_3 not supported")
        elif interval == Interval.MINUTE_5:
            return YFInterval.MIN_5
        elif interval == Interval.MINUTE_10:
            raise ValueError("Interval.MINUTE_10 not supported")
        elif interval == Interval.MINUTE_15:
            return YFInterval.MIN_15
        elif interval == Interval.MINUTE_30:
            return YFInterval.MIN_30
        elif interval == Interval.HOUR:
            return YFInterval.HOUR
        elif interval == Interval.HOUR_2:
            raise ValueError("Interval.HOUR_2 not supported")
        elif interval == Interval.HOUR_3:
            raise ValueError("Interval.HOUR_3 not supported")
        elif interval == Interval.HOUR_4:
            raise ValueError("Interval.HOUR_4 not supported")
        elif interval == Interval.DAY:
            return YFInterval.DAY_1
        elif interval == Interval.WEEK:
            return YFInterval.DAY_5
        elif interval == Interval.MONTH:
            return YFInterval.MONTH_1
