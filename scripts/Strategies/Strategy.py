import logging
import time
import sys
import traceback
from random import shuffle

from Utils import *

class Strategy:
    def __init__(self, config):
        self.positionMap = {}
        # Define common settings in strategies
        self.order_size = config['ig_interface']['order_size']
        self.max_account_usable = config['general']['max_account_usable']
        self.read_configuration(config)


    def spin(self, broker, epic_list):
        logging.info("Strategy started to spin.")
        try:
            # Fetch open positions and process them first
            logging.info("Processing open positions.")
            self.positionMap = broker.get_open_positions()
            if self.positionMap is not None:
                for key, dealSize in self.positionMap.items():
                    epic = key.split('-')[0]
                    self.process_epic(broker, epic)
            else:
                logging.warn("Unable to retrieve open positions!")

            # Start processing all the company in the epic list
            logging.info("Started processing epic list of length: {}".format(len(epic_list)))
            if len(epic_list) < 1:
                logging.warn("Epic list is empty!")
            else:
                shuffle(epic_list)
                for epic in epic_list:
                    try:
                        self.process_epic(broker, epic)
                    except Exception as e:
                        logging.warn(e)
                        logging.warn(traceback.format_exc())
                        logging.warn(sys.exc_info()[0])
                        time.sleep(self.timeout)
                        continue

            # Define timeout until next iteration of strategy
            strategyInteval = 3600 # 1 hour in seconds
            if self.interval == 'HOUR_4':
                strategyInterval = 60 * 60 * 4
            logging.info("Epics analysis complete. Wait for {} seconds".format(strategyInterval))
            time.sleep(strategyInterval)
        except Exception as e:
                logging.warn(e)
                logging.warn(traceback.format_exc())
                logging.warn(sys.exc_info()[0])
                logging.warn("Something fucked up.")
                time.sleep(self.timeout)


    def process_epic(self, broker, epic):
        # Process the epic and find if we want to trade
        trade, limit, stop = self.find_trade_signal(broker, epic)

        # In case of no trade return
        if trade is TradeDirection.NONE:
            time.sleep(self.timeout)
            return
        else:
            # Perform safety check for trade action
            if self.safe_to_trade(broker, epic, trade):
                broker.trade(epic, trade.name, limit, stop)
                time.sleep(self.timeout)


    def safe_to_trade(self, broker, epic, trade):
        # Check if we got another position open for same epic and same direction
        if self.positionMap is not None:
            for key, dealSize in self.positionMap.items():
                epic = key.split('-')[0]
                direction = key.split('-')[1]
                if trade.name == direction:
                    logging.warn("There is already an open position for this epic, skip trade")
                    return False
        else:
            logging.warn("Unable to retrieve open positions! Avoid trading this epic")
            return False

        # Check if the account has enough cash available to open new positions
        balance, deposit = broker.get_account_balances()
        percent_used = percentage(deposit, balance)
        if percent_used > self.max_account_usable:
            logging.warn("Will not trade, {}% of account balance is used."
                            .format(str(percent_used)))
            return False
        else:
            logging.info("Ok to trade, {}% of account is used"
                            .format(str(percent_used)))
            return True
