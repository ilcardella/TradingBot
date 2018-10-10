import logging
import numpy
import pandas

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
        
        # 1 Get past 26 candles (try DAY)
        prices = brokerIf.get_prices(epic_id, 'DAY', 26)
        current_bid, current_offer = brokerIf.get_market_price(epic_id)

        if prices is None or current_bid is None or current_offer is None:
            logging.info('Strategy cannot run: something is wrong with the prices.')
            return None, None, None
        
        # 2 Calculate average close price
        l = []
        for p in prices['prices']:
            l.append(p['closePrice']['bid'])
        df = pandas.DataFrame(l)
        close_12_ema = df.rolling(window=12,min_periods=1,center=False).mean()
        close_26_ema = df.rolling(window=26,min_periods=1,center=False).mean()
        data = (close_12_ema - close_26_ema)
        print(data)
        # close_prices = []
        # for i in prices['prices']:
        #     if i['closePrice']['bid'] is not None:
        #         close_prices.append(i['closePrice']['bid'])
        # long_avg = numpy.average(close_prices)

        # 3 Calculate average of the previous 12 values of the average
        # 4 Calculate the diff
        # 5 Evaluate whether diff is > < = 0
        # 6 Repeat steps 1-5 starting from current market prices backward
        # 7 Compare first diff with second diff
        # 8 Take a decision based on crossing of the two values

       
        return tradeDirection, limit, stop


