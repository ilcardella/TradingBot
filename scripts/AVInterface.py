import requests
import json
import logging
from enum import Enum

class AVTimeSeries(Enum):
    TIME_SERIES_DAILY = 'TIME_SERIES_DAILY',
    TIME_SERIES_INTRADAY = 'TIME_SERIES_INTRADAY'


class AVIntervals(Enum):
    DAILY = 'Daily',
    HOURLY = '60min'
    # TODO add others


class AVPriceType(Enum):
    CLOSE = '4. close'
    # TODO add others


class AVInterface():
    def __init__(self, config, apiKey):
        self.read_configuration(config)
        self.API_KEY = apiKey
        self.apiBaseURL = 'https://www.alphavantage.co/query?'

    def read_configuration(self, config):
        pass

    def get_price_series_raw(self, marketId, function, interval):
        intParam = '&interval={}'.format(interval.value)
        if interval == AVIntervals.DAILY:
            intParam = ''
        url = '{}function={}&symbol={}{}&outputsize=full&apikey={}'.format(self.apiBaseURL, function.value, marketId, intParam, self.API_KEY)
        data = requests.get(url)
        if 'Error Message' in data or 'Information' in data:
            logging.error("AlphaVantage wrong api call for {}".format(marketId))
            return None
        return json.loads(data.text)

    def get_price_series_close(self, marketId, function, interval):
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

    def get_macd_series_raw(self, marketId, interval):
        intParam = 'daily'
        if interval == AVIntervals.DAILY:
            intParam = 'daily'
        elif interval == AVIntervals.HOURLY:
            intParam = '60min'
        url = '{}function=MACD&symbol={}&interval={}&series_type=close&apikey={}'.format(self.apiBaseURL, marketId, intParam, self.API_KEY)
        data = requests.get(url)
        if 'Error Message' in data or 'Information' in data:
            logging.error("AlphaVantage wrong api call for {}".format(marketId))
            return None
        return json.loads(data.text)

    def get_macd_crossings(self, marketId, interval):
        data = self.get_macd_series_raw(marketId, interval)
        if data is not None:
            for ts, value in data['Technical Analysis: MACD'].items():
                pass # Return a list of 1/0 where 1 means crossing
        else:
            return None
