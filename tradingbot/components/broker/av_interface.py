import logging
import sys
import traceback
from enum import Enum

import pandas
from alpha_vantage.techindicators import TechIndicators
from alpha_vantage.timeseries import TimeSeries

from ...interfaces import Market, MarketHistory, MarketMACD
from .. import Interval
from . import StocksInterface


class AVInterval(Enum):
    """
    AlphaVantage interval types: '1min', '5min', '15min', '30min', '60min'
    """

    MIN_1 = "1min"
    MIN_5 = "5min"
    MIN_15 = "15min"
    MIN_30 = "30min"
    MIN_60 = "60min"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class AVInterface(StocksInterface):
    """
    AlphaVantage interface class, provides methods to call AlphaVantage API
    and return the result in useful format handling possible errors.
    """

    def initialise(self) -> None:
        logging.info("Initialising AVInterface...")
        api_key = self._config.get_credentials()["av_api_key"]
        self.TS = TimeSeries(
            key=api_key, output_format="pandas", treat_info_as_error=True
        )
        self.TI = TechIndicators(
            key=api_key, output_format="pandas", treat_info_as_error=True
        )

    def _to_av_interval(self, interval: Interval) -> AVInterval:
        """
        Convert the Broker Interval to AlphaVantage compatible intervals.
        Return the converted interval or None if a conversion is not available
        """
        if interval == Interval.MINUTE_1:
            return AVInterval.MIN_1
        elif interval == Interval.MINUTE_5:
            return AVInterval.MIN_5
        elif interval == Interval.MINUTE_15:
            return AVInterval.MIN_15
        elif interval == Interval.MINUTE_30:
            return AVInterval.MIN_30
        elif interval == Interval.HOUR:
            return AVInterval.MIN_60
        elif interval == Interval.DAY:
            return AVInterval.DAILY
        elif interval == Interval.WEEK:
            return AVInterval.WEEKLY
        elif interval == Interval.MONTH:
            return AVInterval.MONTHLY
        else:
            logging.error(
                "Unable to convert interval {} to AlphaVantage equivalent".format(
                    interval.value
                )
            )
            raise ValueError("Unsupported Interval value: {}".format(interval))

    def get_prices(
        self, market: Market, interval: Interval, data_range: int
    ) -> MarketHistory:
        data = None
        av_interval = self._to_av_interval(interval)
        if (
            av_interval == AVInterval.MIN_1
            or av_interval == AVInterval.MIN_5
            or av_interval == AVInterval.MIN_15
            or av_interval == AVInterval.MIN_30
            or av_interval == AVInterval.MIN_60
        ):
            data = self.intraday(market.id, av_interval)
        elif av_interval == AVInterval.DAILY:
            data = self.daily(market.id)
        elif av_interval == AVInterval.WEEKLY:
            data = self.weekly(market.id)
        # TODO implement monthly call
        else:
            raise ValueError("Unsupported Interval.{}".format(interval.name))
        history = MarketHistory(
            market,
            data.index,
            data["2. high"].values,
            data["3. low"].values,
            data["4. close"].values,
            data["5. volume"].values,
        )
        return history

    def daily(self, marketId: str) -> pandas.DataFrame:
        """
        Calls AlphaVantage API and return the Daily time series for the given market

            - **marketId**: string representing an AlphaVantage compatible market id
            - Returns **None** if an error occurs otherwise the pandas dataframe
        """
        self._wait_before_call(self._config.get_alphavantage_api_timeout())
        market = self._format_market_id(marketId)
        try:
            data, meta_data = self.TS.get_daily(symbol=market, outputsize="full")
            return data
        except Exception as e:
            print(e)
            logging.error("AlphaVantage wrong api call for {}".format(market))
            logging.debug(e)
            logging.debug(traceback.format_exc())
            logging.debug(sys.exc_info()[0])
        return None

    def intraday(self, marketId: str, interval: AVInterval) -> pandas.DataFrame:
        """
        Calls AlphaVantage API and return the Intraday time series for the given market

            - **marketId**: string representing an AlphaVantage compatible market id
            - **interval**: string representing an AlphaVantage interval type
            - Returns **None** if an error occurs otherwise the pandas dataframe
        """
        self._wait_before_call(self._config.get_alphavantage_api_timeout())
        market = self._format_market_id(marketId)
        try:
            data, meta_data = self.TS.get_intraday(
                symbol=market, interval=interval.value, outputsize="full"
            )
            return data
        except Exception as e:
            logging.error("AlphaVantage wrong api call for {}".format(market))
            logging.debug(e)
            logging.debug(traceback.format_exc())
            logging.debug(sys.exc_info()[0])
        return None

    def weekly(self, marketId: str) -> pandas.DataFrame:
        """
        Calls AlphaVantage API and return the Weekly time series for the given market

            - **marketId**: string representing an AlphaVantage compatible market id
            - Returns **None** if an error occurs otherwise the pandas dataframe
        """
        self._wait_before_call(self._config.get_alphavantage_api_timeout())
        market = self._format_market_id(marketId)
        try:
            data, meta_data = self.TS.get_weekly(symbol=market)
            return data
        except Exception as e:
            logging.error("AlphaVantage wrong api call for {}".format(market))
            logging.debug(e)
            logging.debug(traceback.format_exc())
            logging.debug(sys.exc_info()[0])
        return None

    def quote_endpoint(self, market_id: str) -> pandas.DataFrame:
        """
        Calls AlphaVantage API and return the Quote Endpoint data for the given market

            - **market_id**: string representing the market id to fetch data of
            - Returns **None** if an error occurs otherwise the pandas dataframe
        """
        self._wait_before_call(self._config.get_alphavantage_api_timeout())
        market = self._format_market_id(market_id)
        try:
            data, meta_data = self.TS.get_quote_endpoint(
                symbol=market, outputsize="full"
            )
            return data
        except Exception:
            logging.error("AlphaVantage wrong api call for {}".format(market))
        return None

    # Technical indicators

    def get_macd(
        self, market: Market, interval: Interval, datapoints_range: int
    ) -> MarketMACD:
        av_interval = self._to_av_interval(interval)
        data = self.macdext(market.id, av_interval)
        macd = MarketMACD(
            market,
            data.index,
            data["MACD"].values,
            data["MACD_Signal"].values,
            data["MACD_Hist"].values,
        )
        return macd

    def macdext(self, marketId: str, interval: AVInterval) -> pandas.DataFrame:
        """
        Calls AlphaVantage API and return the MACDEXT tech indicator series for the given market

            - **marketId**: string representing an AlphaVantage compatible market id
            - **interval**: string representing an AlphaVantage interval type
            - Returns **None** if an error occurs otherwise the pandas dataframe
        """
        self._wait_before_call(self._config.get_alphavantage_api_timeout())
        market = self._format_market_id(marketId)
        data, meta_data = self.TI.get_macdext(
            market,
            interval=interval.value,
            series_type="close",
            fastperiod=12,
            slowperiod=26,
            signalperiod=9,
            fastmatype=2,
            slowmatype=1,
            signalmatype=0,
        )
        return data

    def macd(self, marketId: str, interval: AVInterval) -> pandas.DataFrame:
        """
        Calls AlphaVantage API and return the MACDEXT tech indicator series for the given market

            - **marketId**: string representing an AlphaVantage compatible market id
            - **interval**: string representing an AlphaVantage interval type
            - Returns **None** if an error occurs otherwise the pandas dataframe
        """
        self._wait_before_call(self._config.get_alphavantage_api_timeout())
        market = self._format_market_id(marketId)
        data, meta_data = self.TI.get_macd(
            market,
            interval=interval.value,
            series_type="close",
            fastperiod=12,
            slowperiod=26,
            signalperiod=9,
        )
        return data

    # Utils functions

    def _format_market_id(self, marketId: str) -> str:
        """
        Convert a standard market id to be compatible with AlphaVantage API.
        Adds the market exchange prefix (i.e. London is LON:)
        """
        # TODO MarketProvider/IGInterface should return marketId without "-UK"
        return "{}:{}".format("LON", marketId.split("-")[0])
