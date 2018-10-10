import logging
import sys
import traceback
import pytz
import datetime
import time
from random import shuffle

from Utils import *
from IGInterface import IGInterface

class StocksAutoTrader:
    def __init__(self, config):
        self.read_configuration(config)
        # Read list of company epic ids
        self.main_epic_ids = self.get_epic_ids()
        # Create IG interface
        self.IG = IGInterface(config)

    def read_configuration(self, config):
        self.order_size = config['ig_interface']['order_size']
        self.time_zone = config['general']['time_zone']
        self.max_account_usable = config['general']['max_account_usable']
        self.spread_filter = config['general']['spread_filter_enabled']
        self.epic_ids_filepath = config['general']['epic_ids_filepath']

    def get_epic_ids(self):
        # define empty list
        epic_ids = []
        try:
            # open file and read the content in a list
            with open(self.epic_ids_filepath, 'r') as filehandle:
                filecontents = filehandle.readlines()
                for line in filecontents:
                    # remove linebreak which is the last character of the string
                    current_epic_id = line[:-1]
                    # add item to the list
                    epic_ids.append(current_epic_id)
        except IOError:
            # Create the file empty
            logging.warn("Epic ids file not found, it will be created empty.")
            filehandle = open(self.epic_ids_filepath, 'w')
        logging.debug(epic_ids)
        return epic_ids
    
    def idTooMuchPositions(self, key, positionMap):
        max_trades = int(int(self.order_size) * 2)
        if((key in positionMap) and (int(positionMap[key]) >= int(max_trades))):
            return True
        else:
            return False

    def isMarketOpen(self, timezone):
        tz = pytz.timezone(timezone)
        now_time = datetime.datetime.now(tz=tz).strftime('%H:%M')
        return is_between(str(now_time), ("07:55", "16:35"))

    def find_good_epics(self, epic_ids):
        spreads_and_epics = []
        pick_from_epics = []
        i_count = 0
        b_TRADE_OK = True

        for epic_id in epic_ids:
            tmp_lst = []
            i_count += 1
            try:
                if b_TRADE_OK:
                    current_bid, ask_price = self.IG.get_market_price(epic_id)
                    time.sleep(1)
                    spread = float(current_bid) - float(ask_price)
                    if float(spread) >= -1:
                        logging.info("Found a good epic: {} ({}/{})".format(epic_id,
                                                                            str(i_count),
                                                                            str(len(epic_ids))))
                        time.sleep(1)
                        pick_from_epics.append(epic_id)
                    else:
                        logging.info("Not a good epic: {} ({}/{})".format(epic_id,
                                                                            str(i_count),
                                                                            str(len(epic_ids))))
                        time.sleep(1)
                        continue

            except Exception as e:
                logging.debug(e)
                logging.info("No data returned: {} ({}/{})".format(epic_id,
                                                                    str(i_count),
                                                                    str(len(epic_ids))))
                pass
        shuffle(pick_from_epics)
        return (pick_from_epics)

    def start(self, argv, strategy):
        if len(argv) != 3: # the first argument is the script name
            logging.error("Wrong number of arguments. Provide username and password`")
            return
        username = sys.argv[1]
        password = sys.argv[2]
        # Init the broker interface
        if not self.IG.authenticate(username, password):
            return

        if len(self.main_epic_ids) < 1:
            # TODO work only on open positions
            logging.warn("Epic list is empty!")
            return

        logging.info('Starting main routine.')

        while True:
            if self.isMarketOpen(self.time_zone):
                logging.info("Market is closed! Wait...")
                time.sleep(60)
                continue
            else:
                if self.spread_filter:
                    # Filter epics to find those with a small spread
                    tradeable_epic_ids = self.find_good_epics(self.main_epic_ids)
                else:
                    tradeable_epic_ids = self.main_epic_ids
                
                if len(tradeable_epic_ids) > 0:
                    for epic_id in tradeable_epic_ids:
                        try:
                            # Run the strategy
                            trade_direction, limitDistance_value, stopDistance_value = strategy.execute(self.IG, epic_id)

                            # In case of no trade skip to next epic
                            if trade_direction == TradeDirection.NONE:
                                continue

                            positionMap = self.IG.get_open_positions()
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
                            #     balance, deposit = self.IG.get_account_balances()
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

                            self.IG.trade(epic_id, trade_direction,
                                                limitDistance_value, stopDistance_value)
                        except Exception as e:
                            logging.info(e)
                            logging.info(traceback.format_exc())
                            logging.info(sys.exc_info()[0])
                            logging.info("Something fucked up.")
                            time.sleep(2)
                            continue
                else:
                    logging.info("No tradable epic found")
                    continue
