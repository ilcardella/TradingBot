import logging
import numpy as np
import pandas as pd
import requests
import json

from .Strategy import Strategy
from Utils import *

class SimpleMACD(Strategy):
    def __init__(self, config):
        super().__init__(config)
        logging.info('Simple MACD strategy initialised.')


    def read_configuration(self, config):
        self.interval = config['strategies']['simple_macd']['interval']
        self.controlledRisk = config['ig_interface']['controlled_risk']
        self.use_av_api = config['strategies']['simple_macd']['use_av_api']
        self.timeout = 1 # Delay between each find_trade_signal() call
        if self.use_av_api:
            try:
                with open('../config/.credentials', 'r') as file:
                    credentials = json.load(file)
                    self.AV_API_KEY = credentials['av_api_key']
                    self.timeout = 10
            except IOError:
                logging.error("Credentials file not found!")
                return


    # TODO  possibly split in more smaller ones
    def find_trade_signal(self, broker, epic_id):
        tradeDirection = TradeDirection.NONE
        limit = None
        stop = None

        # Fetch current market data
        market = broker.get_market_info(epic_id)
        # Safety checks before processing the epic
        if (market is None
            or 'markets' in market
            or market['snapshot']['bid'] is None):
            logging.warn('Strategy can`t process {}'.format(epic_id))
            return TradeDirection.NONE, None, None

        # Extract market data to calculate stop and limit values
        stop_perc = max([market['dealingRules']['minNormalStopOrLimitDistance']['value'], 5])
        if self.controlledRisk:
            stop_perc = market['dealingRules']['minControlledRiskStopDistance']['value'] + 1 # +1 to avoid rejection
        current_bid = market['snapshot']['bid']
        current_offer = market['snapshot']['offer']

        # Extract market Id
        marketId = market['instrument']['marketId']

        # Fetch historic prices and build a list with them ordered cronologically
        hist_data = []
        if self.use_av_api:
            # Convert the string for alpha vantage
            marketIdAV = '{}:{}'.format('LON', marketId.split('-')[0])
            prices = self.get_av_historic_price(marketIdAV, 'TIME_SERIES_DAILY', '1day', self.AV_API_KEY)
            # Safety check
            if 'Error Message' in prices or 'Information' in prices:
                logging.warn('Strategy can`t process {}'.format(marketId))
                return TradeDirection.NONE, None, None
            prevBid = 0
            for ts, values in prices['Time Series (Daily)'].items():
                if values['4. close'] == 0.0:
                    hist_data.insert(0, prevBid)
                else:
                    hist_data.insert(0, values['4. close'])
                    prevBid = values['4. close']
        else:
            prices = broker.get_prices(epic_id, self.interval, 26)
            prevBid = 0
            for p in prices['prices']:
                if p['closePrice']['bid'] is None:
                    hist_data.append(prevBid)
                else:
                    hist_data.append(p['closePrice']['bid'])
                    prevBid = p['closePrice']['bid']
            if prices is None or 'prices' not in prices:
                logging.warn('Strategy can`t process {}'.format(marketId))
                return TradeDirection.NONE, None, None

        # Calculate the MACD indicator and find signals where macd cross its sma(9) average
        px = pd.DataFrame({'close': hist_data})
        px['26_ema'] = pd.DataFrame.ewm(px['close'], span=26).mean()
        px['12_ema'] = pd.DataFrame.ewm(px['close'], span=12).mean()
        px['macd'] = (px['12_ema'] - px['26_ema'])
        px['macd_signal'] = px['macd'].rolling(9).mean()
        px['positions'] = 0
        px.loc[9:, 'positions'] = np.where(px.loc[9:, 'macd'] >= px.loc[9:, 'macd_signal'] , 1, 0)
        px['signals']=px['positions'].diff()

        # Identify the trade direction looking at the last signal
        if len(px['signals']) > 0 and px['signals'].iloc[-1] > 0:
            tradeDirection = TradeDirection.BUY
            limit = current_offer + percentage_of(10, current_offer)
            stop = current_bid - percentage_of(stop_perc, current_bid)
        elif len(px['signals']) > 0 and px['signals'].iloc[-1] < 0:
            tradeDirection = TradeDirection.SELL
            limit = current_bid - percentage_of(10, current_bid)
            stop = current_offer + percentage_of(stop_perc, current_offer)
        else:
            tradeDirection = TradeDirection.NONE
            limit = None
            stop = None

        # Log only tradable epics
        if tradeDirection is not TradeDirection.NONE:
            logging.info("SimpleMACD says: {} {}".format(tradeDirection.name, marketId))

        return tradeDirection, limit, stop


    def get_av_historic_price(self, marketId, function, interval, apiKey):
        intParam = '&interval={}'.format(interval)
        if interval == '1day':
            intParam = ''
        url = 'https://www.alphavantage.co/query?function={}&symbol={}{}&outputsize=full&apikey={}'.format(function, marketId, intParam, apiKey)
        data = requests.get(url)
        return json.loads(data.text)
