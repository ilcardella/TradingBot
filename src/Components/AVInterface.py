import requests
import json
import logging
from enum import Enum
import os
import sys
import inspect
import datetime as dt
import time
import traceback

from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.techindicators import TechIndicators

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)


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


class AVInterface:
    """
    AlphaVantage interface class, provides methods to call AlphaVantage API
    and return the result in useful format handling possible errors.
    """

    def __init__(self, apiKey, config):
        self.read_configuration(config)
        self._last_call_ts = dt.datetime.now()
        self.TS = TimeSeries(
            key=apiKey, output_format="pandas", treat_info_as_error=True
        )
        self.TI = TechIndicators(
            key=apiKey, output_format="pandas", treat_info_as_error=True
        )
        logging.info("AlphaVantage initialised.")

    def read_configuration(self, config):
        self.enable = config["alpha_vantage"]["enable"]
        self.api_timeout = config["alpha_vantage"]["api_timeout"]

    def get_prices(self, market_id, interval):
        """
        Return the price time series of the requested market with the interval
        granularity. Return None if the interval is invalid
        """
        if (
            interval == AVInterval.MIN_1
            or interval == AVInterval.MIN_5
            or interval == AVInterval.MIN_15
            or interval == AVInterval.MIN_30
            or interval == AVInterval.MIN_60
        ):
            return self.intraday(market_id, interval)
        elif interval == AVInterval.DAILY:
            return self.daily(market_id)
        elif interval == AVInterval.WEEKLY:
            return self.weekly(market_id)
        # TODO implement monthly call
        else:
            return None

    def daily(self, marketId):
        """
        Calls AlphaVantage API and return the Daily time series for the given market

            - **marketId**: string representing an AlphaVantage compatible market id
            - Returns **None** if an error occurs otherwise the pandas dataframe
        """
        self._wait_before_call()
        market = self._format_market_id(marketId)
        try:
            data, meta_data = self.TS.get_daily(symbol=market, outputsize="full")
            return data
        except Exception as e:
            logging.error("AlphaVantage wrong api call for {}".format(market))
            logging.debug(e)
            logging.debug(traceback.format_exc())
            logging.debug(sys.exc_info()[0])
        return None

    def intraday(self, marketId, interval):
        """
        Calls AlphaVantage API and return the Intraday time series for the given market

            - **marketId**: string representing an AlphaVantage compatible market id
            - **interval**: string representing an AlphaVantage interval type
            - Returns **None** if an error occurs otherwise the pandas dataframe
        """
        self._wait_before_call()
        if interval is AVIntervals.DAILY:
            logging.error("AlphaVantage Intraday does not support DAILY interval")
            return None
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

    def weekly(self, marketId):
        """
        Calls AlphaVantage API and return the Weekly time series for the given market

            - **marketId**: string representing an AlphaVantage compatible market id
            - Returns **None** if an error occurs otherwise the pandas dataframe
        """
        self._wait_before_call()
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

    def quote_endpoint(self, market_id):
        """
        Calls AlphaVantage API and return the Quote Endpoint data for the given market

            - **market_id**: string representing the market id to fetch data of
            - Returns **None** if an error occurs otherwise the pandas dataframe
        """
        self._wait_before_call()
        market = self._format_market_id(market_id)
        try:
            data, meta_data = self.TS.get_quote_endpoint(
                symbol=market, outputsize="full"
            )
            return data
        except:
            logging.error("AlphaVantage wrong api call for {}".format(market))
        return None

    # Technical indicators

    def macdext(self, marketId, interval):
        """
        Calls AlphaVantage API and return the MACDEXT tech indicator series for the given market

            - **marketId**: string representing an AlphaVantage compatible market id
            - **interval**: string representing an AlphaVantage interval type
            - Returns **None** if an error occurs otherwise the pandas dataframe
        """
        self._wait_before_call()
        market = self._format_market_id(marketId)
        try:
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
            # if data is None:
            #     return None
            # data.index = range(len(data))
            return data
        except Exception as e:
            logging.error("AlphaVantage wrong api call for {}".format(market))
            logging.debug(e)
            logging.debug(traceback.format_exc())
            logging.debug(sys.exc_info()[0])
        return None

    def macd(self, marketId, interval):
        """
        Calls AlphaVantage API and return the MACDEXT tech indicator series for the given market

            - **marketId**: string representing an AlphaVantage compatible market id
            - **interval**: string representing an AlphaVantage interval type
            - Returns **None** if an error occurs otherwise the pandas dataframe
        """
        self._wait_before_call()
        market = self._format_market_id(marketId)
        try:
            data, meta_data = self.TI.get_macd(
                market,
                interval=interval.value,
                series_type="close",
                fastperiod=12,
                slowperiod=26,
                signalperiod=9,
            )
            return data
        except Exception as e:
            logging.error("AlphaVantage wrong api call for {}".format(market))
            logging.debug(e)
            logging.debug(traceback.format_exc())
            logging.debug(sys.exc_info()[0])
        return None

    # Utils functions

    def _format_market_id(self, marketId):
        """
        Convert a standard market id to be compatible with AlphaVantage API.
        Adds the market exchange prefix (i.e. London is LON:)
        """
        return "{}:{}".format("LON", marketId.split("-")[0])

    def _wait_before_call(self):
        """
        Wait between API calls to not overload the server
        """
        while (dt.datetime.now() - self._last_call_ts) <= dt.timedelta(
            seconds=self.api_timeout
        ):
            time.sleep(0.5)
        self._last_call_ts = dt.datetime.now()
