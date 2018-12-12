import logging
import time
import traceback
from random import shuffle
import os
import inspect
import sys

currentdir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from Utils import Utils, TradeDirection


class Strategy:
    """
    Generic strategy template to use as a parent class for custom strategies.
    Provide safety checks for new trades and handling of open positions.
    """

    def __init__(self, config, services):
        self.positions = {}
        self.broker = services['broker']
        self.AV = services['alpha_vantage']

        # This can be overwritten in children class
        self.spin_interval = config['strategies']['spin_interval']
        self.timeout = 1  # Delay between each find_trade_signal() call

        # This must be the last operation of this function to override possible values in children class
        self.read_configuration(config)


#############################################################
# OVERRIDE THESE FUNCTIONS IN STRATEGY IMPLEMENTATION
#############################################################

    def read_configuration(self, config):
        """
        Must override
        """
        raise NotImplementedError('Not implemented: read_configuration')

    def find_trade_signal(self, epic_id):
        """
        Must override
        """
        raise NotImplementedError('Not implemented: find_trade_signal')

    def get_seconds_to_next_spin(self):
        """
        Must override
        """
        return self.spin_interval

##############################################################
##############################################################
