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
    def __init__(self, config):
        self.read_configuration(config)

    def read_configuration(self, config):
        self.strategies = config['strategies']

    def make_strategy(self, strategy_name, config=None, services=None):
        if strategy_name == StrategyNames.SIMPLE_MACD.value:
            return SimpleMACD(config, services)
        elif strategy_name == StrategyNames.FAIG.value:
            return FAIG_iqr(config, services)
        else:
            logging.error('Impossible to create strategy {}. It does not exist'.format(strategy_name))
