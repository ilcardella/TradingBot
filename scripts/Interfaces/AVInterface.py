import requests
import json
import logging
from enum import Enum
import os
import sys
import inspect

from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.techindicators import TechIndicators

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)


class AVIntervals(Enum):
    """
    AlphaVantage interval types: '1min', '5min', '15min', '30min', '60min'
    """
    DAILY = 'daily',
    MIN_60 = '60min',
    MIN_30 = '30min',
    MIN_15 = '15min',
    MIN_5 = '5min',
    MIN_1 = '1min'


class AVInterface():
    """
    AlphaVantage interface class, provides methods to call AlphaVantage API
    and return the result in useful format handling possible errors.
    """

    def __init__(self, apiKey):
        self.TS = TimeSeries(
            key=apiKey, output_format='pandas', indexing_type='integer', treat_info_as_error=True)
        self.TI = TechIndicators(key=apiKey, output_format='pandas')
        logging.info('AlphaVantage initialised.')

    def daily(self, marketId):
        """
        Calls AlphaVantage API and return the Daily time series for the given market

            - **marketId**: string representing an AlphaVantage compatible market id
            - Returns **None** if an error occurs otherwise the pandas dataframe
        """
        market = _format_market_id(marketId)
        try:
            data, meta_data = self.TS.get_daily(
                symbol=market, outputsize='full')
            return data
        except:
            logging.error(
                "AlphaVantage wrong api call for {}".format(marketId))
        return None

    def intraday(self, marketId, interval):
        """
        Calls AlphaVantage API and return the Intraday time series for the given market

            - **marketId**: string representing an AlphaVantage compatible market id
            - **interval**: string representing an AlphaVantage interval type
            - Returns **None** if an error occurs otherwise the pandas dataframe
        """
        if (interval is AVIntervals.DAILY):
            logging.error(
                "AlphaVantage Intraday does not support DAILY interval")
            return None
        market = _format_market_id(marketId)
        try:
            data, meta_data = self.TS.get_intraday(
                symbol=market, interval=interval.value, outputsize='full')
            return data
        except:
            logging.error(
                "AlphaVantage wrong api call for {}".format(marketId))
        return None

    def macdext(self, marketId, interval):
        """
        Calls AlphaVantage API and return the MACDEXT tech indicator series for the given market

            - **marketId**: string representing an AlphaVantage compatible market id
            - **interval**: string representing an AlphaVantage interval type
            - Returns **None** if an error occurs otherwise the pandas dataframe
        """
        market = self._format_market_id(marketId)
        try:
            data, meta_data = self.TI.get_macdext(market, interval=interval.value, series_type='close',
                                                  fastperiod=12, slowperiod=26, signalperiod=9, fastmatype=2,
                                                  slowmatype=1, signalmatype=0)
            return data
        except:
            logging.error(
                "AlphaVantage wrong api call for {}".format(marketId))
        return None

    def macd(self, marketId, interval):
        """
        Calls AlphaVantage API and return the MACDEXT tech indicator series for the given market

            - **marketId**: string representing an AlphaVantage compatible market id
            - **interval**: string representing an AlphaVantage interval type
            - Returns **None** if an error occurs otherwise the pandas dataframe
        """
        market = self._format_market_id(marketId)
        try:
            data, meta_data = self.TI.get_macd(market, interval=interval.value, series_type='close',
                                               fastperiod=12, slowperiod=26, signalperiod=9)
            return data
        except:
            logging.error(
                "AlphaVantage wrong api call for {}".format(marketId))
        return None

    def _format_market_id(self, marketId):
        """
        Convert a standard market id to be compatible with AlphaVantage API.
        Adds the market exchange prefix (i.e. London is LON:)
        """
        return '{}:{}'.format('LON', marketId.split('-')[0])
