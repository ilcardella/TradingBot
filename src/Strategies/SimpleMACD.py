import logging
import numpy as np
import os
import inspect
import sys
from datetime import datetime

currentdir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from Interfaces.AVInterface import AVIntervals
from .Strategy import Strategy
from Utils import Utils, TradeDirection


class SimpleMACD(Strategy):
    """
    Strategy that use the MACD technical indicator of a market to decide whether
    to buy, sell or hold.
    Buy when the MACD cross over the MACD signal.
    Sell when the MACD cross below the MACD signal.
    """

    def __init__(self, config, broker):
        super().__init__(config, broker)
        logging.info('Simple MACD strategy initialised.')

    def read_configuration(self, config):
        """
        Read the json configuration
        """
        self.spin_interval = config['strategies']['simple_macd']['spin_interval']
        self.controlledRisk = config['ig_interface']['controlled_risk']
        self.use_av_api = config['general']['use_av_api']
        self.max_spread_perc = config['strategies']['simple_macd']['max_spread_perc']
        self.limit_p = config['strategies']['simple_macd']['limit_perc']
        self.stop_p = config['strategies']['simple_macd']['stop_perc']


    def find_trade_signal(self, epic_id):
        """
        Calculate the MACD of the previous days and find a cross between MACD
        and MACD signal

            - **epic_id**: market epic as string
            - Returns TradeDirection, limit_level, stop_level or TradeDirection.NONE, None, None
        """
        # Fetch data for the market
        marketId, current_bid, current_offer, limit_perc, stop_perc = self.get_market_snapshot(
            epic_id)

        # Spread constraint
        if current_bid - current_offer > self.max_spread_perc:
            return TradeDirection.NONE, None, None

        # Fetch historic prices and build a list with them ordered cronologically
        #px = self.get_dataframe_from_historic_prices(marketId, epic_id)
        px = self.broker.macd_dataframe(epic_id, marketId, AVIntervals.DAILY)

        # Find where macd and signal cross each other
        px = self.generate_signals_from_dataframe(px)

        # Identify the trade direction looking at the last signal
        tradeDirection = self.get_trade_direction_from_signals(px)
        # Log only tradable epics
        if tradeDirection is not TradeDirection.NONE:
            logging.info("SimpleMACD says: {} {}".format(
                tradeDirection.name, marketId))

        # Calculate stop and limit distances
        limit, stop = self.calculate_stop_limit(
            tradeDirection, current_offer, current_bid, limit_perc, stop_perc)
        return tradeDirection, limit, stop


    def calculate_stop_limit(self, tradeDirection, current_offer, current_bid, limit_perc, stop_perc):
        """
        Calculate the stop and limit levels from the given percentages
        """
        limit = None
        stop = None
        if tradeDirection == TradeDirection.BUY:
            limit = current_offer + \
                Utils.percentage_of(limit_perc, current_offer)
            stop = current_bid - Utils.percentage_of(stop_perc, current_bid)
        elif tradeDirection == TradeDirection.SELL:
            limit = current_bid - Utils.percentage_of(limit_perc, current_bid)
            stop = current_offer + \
                Utils.percentage_of(stop_perc, current_offer)
        return limit, stop


    def get_seconds_to_next_spin(self):
        """
        Calculate the amount of seconds to wait for between each strategy spin
        """
        # Run this strategy at market opening
        return Utils.get_seconds_to_market_opening(datetime.now())


    def get_market_snapshot(self, epic_id):
        """
        Fetch a market snapshot from the given epic id, and returns
        the **marketId** and the bid/offer prices

            - **epic_id**: market epic as string
            - Returns marketId, bidPrice, offerPrice
        """
        # Fetch current market data
        market = self.broker.get_market_info(epic_id)
        # Safety checks
        if (market is None
            or 'markets' in market  # means that epic_id is wrong
                or market['snapshot']['bid'] is None
                or market['snapshot']['offer'] is None):
            raise Exception

        limit_perc = self.limit_p
        stop_perc = max(
            [market['dealingRules']['minNormalStopOrLimitDistance']['value'], self.stop_p])
        if self.controlledRisk:
            # +1 to avoid rejection
            stop_perc = market['dealingRules']['minControlledRiskStopDistance']['value'] + 1
        # Extract market Id
        marketId = market['instrument']['marketId']
        current_bid = market['snapshot']['bid']
        current_offer = market['snapshot']['offer']

        return marketId, current_bid, current_offer, limit_perc, stop_perc


    def generate_signals_from_dataframe(self, dataframe):
        dataframe['positions'] = 0
        #px.loc[9:, 'positions'] = np.where(px.loc[9:, 'MACD'] >= px.loc[9:, 'MACD_Signal'] , 1, 0)
        dataframe.loc[9:, 'positions'] = np.where(dataframe.loc[9:, 'MACD_Hist'] >= 0, 1, 0)
        # Highlight the direction of the crossing
        dataframe['signals'] = dataframe['positions'].diff()
        return dataframe


    def get_trade_direction_from_signals(self, dataframe):
        tradeDirection = TradeDirection.NONE
        if len(dataframe['signals']) > 0 and dataframe['signals'].iloc[-1] > 0:
            tradeDirection = TradeDirection.BUY
        elif len(dataframe['signals']) > 0 and dataframe['signals'].iloc[-1] < 0:
            tradeDirection = TradeDirection.SELL
        return tradeDirection
