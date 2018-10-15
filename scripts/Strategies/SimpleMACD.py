import logging
import numpy as np
import pandas as pd
import time
import sys
import traceback

from .Strategy import Strategy
from Utils import *

class SimpleMACD(Strategy):
    def __init__(self, config):
        super().__init__(config)
        self.read_configuration(config)
        logging.info('Simple MACD strategy initialised.')


    def read_configuration(self, config):
        self.interval = config['strategies']['simple_macd']['interval']
        self.controlledRisk = config['ig_interface']['controlled_risk']
        self.timeout = 1


    # TODO  possibly split in more smaller ones
    def find_trade_signal(self, broker, epic_id):
        tradeDirection = TradeDirection.NONE
        limit = None
        stop = None

        # Collect data from the broker interface
        prices = broker.get_prices(epic_id, self.interval, 30)
        market = broker.get_market_info(epic_id)

        # Safety checks before processing the epic
        if (prices is None or 'prices' not in prices
            or market is None or 'markets' in market
            or market['snapshot']['bid'] is None):
            logging.warn('Strategy can`t process {}'.format(epic_id))
            return TradeDirection.NONE, None, None

        # Create a list of close prices
        data = []
        prevBid = 0
        for p in prices['prices']:
            if p['closePrice']['bid'] is None:
                data.append(prevBid)
            else:
                data.append(p['closePrice']['bid'])
            prevBid = p['closePrice']['bid']

        # Calculate the MACD indicator and find signals where macd cross its sma(9) average
        px = pd.DataFrame({'close': data})
        px['26_ema'] = pd.DataFrame.ewm(px['close'], span=26).mean()
        px['12_ema'] = pd.DataFrame.ewm(px['close'], span=12).mean()
        px['macd'] = (px['12_ema'] - px['26_ema'])
        px['macd_signal'] = px['macd'].rolling(9).mean()
        px['positions'] = 0
        px['positions'][9:]=np.where(px['macd'][9:]>=px['macd_signal'][9:],1,0)
        px['signals']=px['positions'].diff()

        # Identify the trade direction looking at the last signal
        if len(px['signals']) > 0 and px['signals'].iloc[-1] > 0:
            tradeDirection = TradeDirection.BUY
        elif len(px['signals']) > 0 and px['signals'].iloc[-1] < 0:
            tradeDirection = TradeDirection.SELL
        else:
            tradeDirection = TradeDirection.NONE

        # Extract market data to calculate stop and limit values
        key = 'minNormalStopOrLimitDistance'
        if self.controlledRisk:
            key = 'minControlledRiskStopDistance'
        stop_perc = market['dealingRules'][key]['value'] + 1 # +1 to avoid rejection
        current_bid = market['snapshot']['bid']
        limit = current_bid + percentage_of(10, current_bid)
        stop = current_bid - percentage_of(stop_perc, current_bid)

        # Log only tradable epics
        if tradeDirection is not TradeDirection.NONE:
            logging.info("SimpleMACD says: {} {}".format(tradeDirection, epic_id))

        return tradeDirection, limit, stop
