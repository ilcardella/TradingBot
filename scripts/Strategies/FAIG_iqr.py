import logging
import numpy
import pandas
from scipy import stats
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import math

from .Strategy import Strategy
from Utils import *

class FAIG_iqr(Strategy):
    def __init__(self, config):
        super().__init__(config)
        logging.info('FAIG IQR strategy initialised.')

    def read_configuration(self, config):
        self.esmaStocksMargin = config['general']['esma_stocks_margin_perc']
        self.stopLossMultiplier = config['strategies']['faig']['stop_loss_multiplier']
        self.tooHighMargin = config['strategies']['faig']['too_high_margin']

    # TODO define the spin() method
    # TODO update with new version
