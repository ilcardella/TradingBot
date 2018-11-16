import requests
import json
import logging
from enum import Enum

from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.techindicators import TechIndicators


class AVTimeSeries(Enum):
    """
    AlphaVantage time series types: Daily, Intraday, etc.
    """
    TIME_SERIES_DAILY = 'TIME_SERIES_DAILY',
    TIME_SERIES_INTRADAY = 'TIME_SERIES_INTRADAY'


class AVIntervals(Enum):
    """
    AlphaVantage interval types: Daily, Hourly, 10 minutes, etc.
    """
    DAILY = 'Daily',
    HOURLY = '60min'
    # TODO add others


class AVPriceType(Enum):
    """
    AlphaVantage json price types
    """
    CLOSE = '4. close'
    # TODO add others


class AVInterface():
    """
    AlphaVantage interface class, provides methods to call AlphaVantage API
    and return the result in useful format handling possible errors.
    """
    API_KEY = ''
    apiBaseURL = 'https://www.alphavantage.co/query?'
    TS = None  # TimeSeries
    TI = None  # TechIndicators

    def __init__(self, apiKey):
        AVInterface.API_KEY = apiKey
        AVInterface.TS = TimeSeries(
            key=apiKey, output_format='pandas', indexing_type='integer', treat_info_as_error=True)
        AVInterface.TI = TechIndicators(key=apiKey, output_format='pandas')

    @staticmethod
    def get_price_series_raw(marketId, function, interval):
        """
        Calls AlphaVantage API and fetch historic prices for the given market

            - **marketId**: string representing an AlphaVantage compatible market id
            - **function**: string representing an AlphaVantage time series
            - **interval**: string representing an AlphaVantage interval type
            - Returns **None** if an error occurs otherwise the json object with the price series
        """
        intParam = '&interval={}'.format(interval.value)
        if interval == AVIntervals.DAILY:
            intParam = ''
        url = '{}function={}&symbol={}{}&outputsize=full&apikey={}'.format(
            AVInterface.apiBaseURL, function.value, marketId, intParam, AVInterface.API_KEY)
        data = requests.get(url)
        if 'Error Message' in data or 'Information' in data or 'Note' in data:
            logging.error(
                "AlphaVantage wrong api call for {}".format(marketId))
            return None
        return json.loads(data.text)

    @staticmethod
    def get_price_series_close(marketId, function, interval):
        """
        Calls AlphaVantage API and return a list of past close prices for the given market

            - **marketId**: string representing an AlphaVantage compatible market id
            - **function**: string representing an AlphaVantage time series
            - **interval**: string representing an AlphaVantage interval type
            - Returns **None** if an error occurs otherwise a list of past *close* prices
        """
        hist_data = []
        priceType = AVPriceType.CLOSE.value
        # Fetch price series
        series = self.get_price_series_raw(marketId, function, interval)
        # Build close prices list handling 0 values
        if series is not None:
            prevBid = 0
            for ts, values in series['Time Series ({})'.format(interval.value)].items():
                if values[priceType] == 0.0:
                    hist_data.insert(0, prevBid)
                else:
                    hist_data.insert(0, values[priceType])
                    prevBid = values[priceType]
            return hist_data
        else:
            return None

    @staticmethod
    def get_macd_series_raw(marketId, interval):
        """
        Calls AlphaVantage API and return the MACD tech indicator series for the given market

            - **marketId**: string representing an AlphaVantage compatible market id
            - **interval**: string representing an AlphaVantage interval type
            - Returns **None** if an error occurs otherwise json object with MACD series
        """
        intParam = 'daily'
        if interval == AVIntervals.DAILY:
            intParam = 'daily'
        elif interval == AVIntervals.HOURLY:
            intParam = '60min'
        url = '{}function=MACD&symbol={}&interval={}&series_type=close&apikey={}'.format(
            AVInterface.apiBaseURL, marketId, intParam, AVInterface.API_KEY)
        data = requests.get(url)
        if 'Error Message' in data or 'Information' in data or 'Note' in data:
            logging.error(
                "AlphaVantage wrong api call for {}".format(marketId))
            return None
        return json.loads(data.text)

    @staticmethod
    def macdext(marketId, interval):
        """
        Calls AlphaVantage API and return the MACDEXT tech indicator series for the given market

            - **marketId**: string representing an AlphaVantage compatible market id
            - **interval**: string representing an AlphaVantage interval type
            - Returns **None** if an error occurs otherwise the pandas dataframe
        """
        intParam = 'daily'
        if interval == AVIntervals.DAILY:
            intParam = 'daily'
        elif interval == AVIntervals.HOURLY:
            intParam = '60min'

        try:
            data, meta_data = AVInterface.TI.get_macdext(AVInterface._format_market_id(marketId), interval=intParam, series_type='close',
                                                         fastperiod=12, slowperiod=26, signalperiod=9, fastmatype=2,
                                                         slowmatype=1, signalmatype=0)
            return data
        except:
            logging.error(
                "AlphaVantage wrong api call for {}".format(marketId))
        return None

    def _format_market_id(marketId):
        """
        Convert a standard market id to be compatible with AlphaVantage API.
        Adds the market exchange prefix (i.e. London is LON:)
        """
        return '{}:{}'.format('LON', marketId.split('-')[0])
