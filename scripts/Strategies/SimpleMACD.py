import logging
import numpy as np
import pandas as pd
import time
import sys
import traceback

from .Strategy import Strategy
from Utils import *

class SimpleMACD(Strategy):
    def __init__(self, config):
        self.read_configuration(config)
        logging.info('Simple MACD strategy initialised.')


    def read_configuration(self, config):
        self.order_size = config['ig_interface']['order_size']
        self.max_account_usable = config['general']['max_account_usable']
        self.interval = config['strategies']['simple_macd']['interval']
        self.timeout = 1


    def spin(self, broker, epic_list):
        logging.info("Simple MACD starting to spin.")
        if len(epic_list) < 1:
            # TODO monitor only open positions
            logging.warn("Epic list is empty!")
            return

        for epic in epic_list:
            try:
                # Process the epic and find if we want to trade
                trade, limit, stop = self.process_epic(broker, epic)

                # In case of no trade skip to next epic
                if trade is TradeDirection.NONE:
                    time.sleep(self.timeout)
                    continue
                else:
                    # Perform safety check for trade action
                    if self.safe_to_trade(broker, epic, trade):
                        broker.trade(epic, trade.name, limit, stop)
                        time.sleep(self.timeout)
                    else:
                        # Skip to next epic
                        continue
            except Exception as e:
                logging.warn(e)
                logging.warn(traceback.format_exc())
                logging.warn(sys.exc_info()[0])
                logging.warn("Something fucked up.")
                time.sleep(self.timeout)
                continue


    def process_epic(self, broker, epic_id):
        tradeDirection = TradeDirection.NONE
        limit = None
        stop = None

        prices = broker.get_prices(epic_id, self.interval, 30)
        current_bid, current_offer = broker.get_market_price(epic_id)

        if prices is None or current_bid is None or current_offer is None:
            logging.warn('Strategy can`t process {}'.format(epic_id))
            return TradeDirection.NONE, None, None

        data = []
        for p in prices['prices']:
            data.append(p['closePrice']['bid'])
        data.append(current_bid)

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

        if tradeDirection is not TradeDirection.NONE:
            logging.info("SimpleMACD says: {} {}".format(tradeDirection, epic_id))

        return tradeDirection, limit, stop


    def safe_to_trade(self, broker, epic, trade):
        # Retrieve the current open positions to do safety checks
        positionMap = broker.get_open_positions()

        # Check if we have already a position with same direction
        key = epic + '-' + trade.name
        if key in positionMap and int(positionMap[key]) >= self.order_size:
            logging.warn("{} has {} positions open already, hence should not trade"
                                    .format(str(key), str(positionMap[key])))
            return False

        # Check if it's a signal to exit an open position
        entryDirection = None
        if trade is TradeDirection.BUY:
            entryDirection = TradeDirection.SELL
        elif trade is TradeDirection.SELL:
            entryDirection = TradeDirection.BUY
        else:
            logging.error("Trying to trade with direction NONE!!!!")
            return False

        entryKey = epic + '-' + entryDirection.name
        if entryKey in positionMap:
            return True
        else:
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
