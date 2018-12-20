import logging
import os
import inspect
import sys

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

from .Strategy import Strategy
from Utils import *

class FAIG_iqr(Strategy):
    def __init__(self, config, services):
        super().__init__(config, services)
        logging.info('FAIG IQR strategy initialised.')

    def read_configuration(self, config):
        pass

    def find_trade_signal(self, broker, epic_id):
        tradeDirection = TradeDirection.NONE
        limit = None
        stop = None

        # TODO update with new version

        # Log only tradable epics
        if tradeDirection is not TradeDirection.NONE:
            logging.info("FAIG_iqr says: {} {}".format(tradeDirection, epic_id))

        return tradeDirection, limit, stop
