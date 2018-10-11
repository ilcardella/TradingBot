import logging
import numpy as np
import pandas as pd
import talib as ta

from Utils import *

class SimpleMACD:
    def __init__(self, config):
        self.read_configuration(config)
        logging.info('Simple MACD strategy will be used.')

    def read_configuration(self, config):
        #self.param = config['strategies']['simple_macd']['param']
        pass

    def execute(self, brokerIf, epic_id):
        tradeDirection = TradeDirection.NONE
        limit = None
        stop = None
        
        prices = brokerIf.get_prices(epic_id, 'DAY', 30)
        current_bid, current_offer = brokerIf.get_market_price(epic_id)

        if prices is None or current_bid is None or current_offer is None:
            logging.info('Strategy cannot run: something is wrong with the prices.')
            return None, None, None
        
        data = []
        for p in prices['prices']:
            data.append(p['closePrice']['bid'])

        px = pd.DataFrame({'close': data})
        px['26_ema'] = pd.DataFrame.ewm(px['close'], span=26).mean()
        px['12_ema'] = pd.DataFrame.ewm(px['close'], span=12).mean()

        px['macd'] = (px['12_ema'] - px['26_ema'])
        px['macd_signal'] = px['macd'].rolling(9).mean()

        px['positions'] = 0
        px['positions'][9:]=np.where(px['macd'][9:]>=px['macd_signal'][9:],1,0)
        px['signals']=px['positions'].diff()

        if px['signals'].iloc[-1] > 0:
            tradeDirection = TradeDirection.BUY
        elif px['signals'].iloc[-1] < 0:
            tradeDirection = TradeDirection.SELL
        else:
            tradeDirection = TradeDirection.NONE

        limit = current_bid + percentage_of(10, current_bid)
        stop = current_bid - percentage_of(5, current_bid)

        logging.info("{} {} with limit={} and stop={}".format(tradeDirection,
                                                                epic_id, limit, stop))

        return tradeDirection, limit, stop


