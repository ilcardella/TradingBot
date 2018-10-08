import logging

from Utils import *

class SimpleMACD:
    def __init__(self, config):
        self.read_configuration(config)
        logging.info('Simple MACD strategy will be used.')

    def read_configuration(self, config):
        pass

    def execute(self, brokerIf, epic_id):
        tradeDirection = TradeDirection.NONE
        limit = None
        stop = None
        # TODO
        # 1 Get past 26 candles (try DAY)
        # 2 Calculate average close price
        # 3 Calculate average of the previous 12 values of the average
        # 4 Calculate the diff
        # 5 Evaluate whether diff is > < = 0
        # 6 Repeat steps 1-5 starting from current market prices backward
        # 7 Compare first diff with second diff
        # 8 Take a decision based on crossing of the two values
        return tradeDirection, limit, stop