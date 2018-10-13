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
        logging.info('Simple MACD strategy will be used.')

    def read_configuration(self, config):
        self.order_size = config['ig_interface']['order_size']
        self.max_account_usable = config['general']['max_account_usable']
        self.interval = config['simple_macd']['interval']

    def spin(self, broker, epic_list):
        if len(epic_list) < 1:
            # TODO monitor only open positions
            logging.warn("Epic list is empty!")
            return

        for epic in epic_list:
            try:
                trade_direction, limitDistance_value, stopDistance_value = self.process_epic(broker, epic)

                # In case of no trade skip to next epic
                if trade_direction == TradeDirection.NONE:
                    time.sleep(1)
                    continue

                positionMap = broker.get_open_positions()
                # Check if we have too many positions on this epic
                key = epic_id + '-' + trade_direction
                if self.idTooMuchPositions(key, positionMap):
                    logging.info("{} has {} positions open already, hence should not trade"
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

                if trade_direction is not TradeDirection.NONE:
                    broker.trade(epic_id, trade_direction, limitDistance_value, stopDistance_value)

                time.sleep(1)
            except Exception as e:
                logging.warn(e)
                logging.warn(traceback.format_exc())
                logging.warn(sys.exc_info()[0])
                logging.warn("Something fucked up.")
                time.sleep(1)
                continue


    def process_epic(self, broker, epic_id):
        tradeDirection = TradeDirection.NONE
        limit = None
        stop = None

        prices = broker.get_prices(epic_id, self.interval, 30)
        current_bid, current_offer = broker.get_market_price(epic_id)

        if prices is None or current_bid is None or current_offer is None:
            logging.info('Strategy cannot run: something is wrong with the prices.')
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

        logging.info("{} {} with limit={} and stop={}".format(tradeDirection,
                                                                epic_id, limit, stop))

        return TradeDirection.NONE, None, None#tradeDirection, limit, stop

    def idTooMuchPositions(self, key, positionMap):
        max_trades = int(int(self.order_size))
        if((key in positionMap) and (int(positionMap[key]) >= int(max_trades))):
            return True
        else:
            return False
