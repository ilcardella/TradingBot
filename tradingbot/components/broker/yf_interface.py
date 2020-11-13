import logging
from enum import Enum

import yfinance as yf

from ...interfaces import Market, MarketHistory, MarketMACD
from .. import Interval, Utils
from . import StocksInterface


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
    def initialise(self) -> None:
        logging.info("Initialising YFinanceInterface...")

    def get_prices(
        self, market: Market, interval: Interval, data_range: int
    ) -> MarketHistory:
        self._wait_before_call(self._config.get_yfinance_api_timeout())

        ticker = yf.Ticker(self._format_market_id(market.id))
        data = ticker.history(
            period=self._to_yf_data_range(data_range),
            interval=self._to_yf_interval(interval).value,
        )
        # Reverse dataframe to have most recent data at the top
        data = data.iloc[::-1]
        history = MarketHistory(
            market,
            data.index,
            data["High"].values,
            data["Low"].values,
            data["Close"].values,
            data["Volume"].values,
        )
        return history

    def get_macd(
        self, market: Market, interval: Interval, data_range: int
    ) -> MarketMACD:
        self._wait_before_call(self._config.get_yfinance_api_timeout())
        # Fetch prices with at least 26 data points
        prices = self.get_prices(market, interval, 30)
        data = Utils.macd_df_from_list(
            prices.dataframe[MarketHistory.CLOSE_COLUMN].values
        )
        # TODO use dates instead of index
        return MarketMACD(
            market,
            data.index,
            data["MACD"].values,
            data["Signal"].values,
            data["Hist"].values,
        )

    def _format_market_id(self, market_id: str) -> str:
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
        raise ValueError("Unsupported interval {}".format(interval.name))

    def _to_yf_data_range(self, days: int) -> str:
        # Values: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        if days < 2:
            return "1d"
        elif days < 6:
            return "5d"
        elif days < 32:
            return "1mo"
        elif days < 93:
            return "3mo"
        elif days < 186:
            return "6mo"
        elif days < 366:
            return "1y"
        elif days < 732:
            return "2y"
        elif days < 1830:
            return "5y"
        elif days < 3660:
            return "10y"
        else:
            return "max"
