import os
import sys
import inspect
from enum import Enum
import logging

currentdir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from .SimpleMACD import SimpleMACD
from .FAIG_iqr import FAIG_iqr

class StrategyNames(Enum):
    SIMPLE_MACD = 'simple_macd'
    FAIG = 'faig'

class StrategyFactory:
    def __init__(self, config, services):
        self.read_configuration(config)
        self.config = config
        self.services = services

    def read_configuration(self, config):
        pass

    def make_strategy(self, strategy_name):
        if strategy_name == StrategyNames.SIMPLE_MACD.value:
            return SimpleMACD(self.config, self.services)
        elif strategy_name == StrategyNames.FAIG.value:
            return FAIG_iqr(self.config, self.services)
        else:
            logging.error('Impossible to create strategy {}. It does not exist'.format(strategy_name))
