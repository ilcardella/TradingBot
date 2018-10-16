import logging
import numpy as np
import pandas as pd
import time
import sys
import traceback
from random import shuffle

from .Strategy import Strategy
from Utils import *

class SimpleMACD(Strategy):
    def __init__(self, config):
        super().__init__(config)
        logging.info('Simple MACD strategy initialised.')


    def read_configuration(self, config):
        self.interval = config['strategies']['simple_macd']['interval']
        self.controlledRisk = config['ig_interface']['controlled_risk']
        self.timeout = 1

    # TODO make as generic as possible and move in Strategy class
    def spin(self, broker, epic_list):
        logging.info("Strategy started to spin.")
        try:
            # Fetch open positions and process them first
            positionMap = broker.get_open_positions()
            logging.info("Processing open positions: {}".format(positionMap))
            for key, dealSize in positionMap.items():
                epic = positionMap[key].split('-')[0]
                self.process_epic(broker, epic)

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

    # TODO make as generic as possible and move in Strategy class
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

    # TODO This should be the only function in this class, possibly split in more smaller ones
    def find_trade_signal(self, broker, epic_id):
        tradeDirection = TradeDirection.NONE
        limit = None
        stop = None

        # Collect data from the broker interface
        prices = broker.get_prices(epic_id, self.interval, 30)
        market = broker.get_market_info(epic_id)

        # Safety checks before processing the epic
        if (prices is None or 'prices' not in prices
            or market is None or 'markets' in market):
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

    # TODO make as generic as possible and move in Strategy class
    def safe_to_trade(self, broker, epic, trade):
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
