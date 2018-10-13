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
                trade, limit, stop = self.process_epic(broker, epic)

                # In case of no trade skip to next epic
                if trade is TradeDirection.NONE:
                    time.sleep(self.timeout)
                    continue
                else:
                    # Check if we have already an open position for this epic
                    positionMap = broker.get_open_positions()
                    key = epic + '-' + trade.name
                    if self.idTooMuchPositions(key, positionMap):
                        logging.warn("{} has {} positions open already, hence should not trade"
                                                .format(str(key), str(positionMap[key])))
                        continue

                    # TODO This is commented out now but we need to do this check
                    # and prevent the trade only if the strategy is trying to make us
                    # open a new position. In case of close position trade we should go through
                    #
                    # try:
                    #     # Check if the account has enough cash available to trade
                    #     balance, deposit = broker.get_account_balances()
                    #     percent_used = percentage(deposit, balance)
                    #     if float(percent_used) > self.max_account_usable:
                    #         logging.info("Will not trade, {}% of account balance is used. Waiting..."
                    #                         .format(str(percent_used)))
                    #         time.sleep(60)
                    #         continue
                    #     else:
                    #         logging.info("Ok to trade, {}% of account is used"
                    #                         .format(str(percent_used)))
                    # except Exception as e:
                    #     logging.debug(e)
                    #     logging.warn("Unable to retrieve account balances.")
                    #     continue

                    if trade is not TradeDirection.NONE:
                        broker.trade(epic, trade.name, limit, stop)
                    time.sleep(self.timeout)
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

        return (tradeDirection, limit, stop)

    def idTooMuchPositions(self, key, positionMap):
        max_trades = int(int(self.order_size))
        if((key in positionMap) and (int(positionMap[key]) >= int(max_trades))):
            return True
        else:
            return False
