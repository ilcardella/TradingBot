import logging
import numpy as np
import pandas as pd
import requests
import os
import inspect
import sys

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

    def __init__(self, config, services):
        super().__init__(config, services)
        logging.info('Simple MACD strategy initialised.')

    def read_configuration(self, config):
        """
        Read the json configuration
        """
        self.spin_interval = config['strategies']['simple_macd']['spin_interval']
        self.controlledRisk = config['ig_interface']['controlled_risk']
        self.use_av_api = config['general']['use_av_api']


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

        # Fetch historic prices and build a list with them ordered cronologically
        # TODO unify marketId and epic_id
        px = self.get_dataframe_from_historic_prices(marketId, epic_id)

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
        return Utils.get_seconds_to_market_opening()


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

        # TODO make limit and stop configurable or depending on market data
        limit_perc = 15
        stop_perc = max(
            [market['dealingRules']['minNormalStopOrLimitDistance']['value'], 8])
        if self.controlledRisk:
            # +1 to avoid rejection
            stop_perc = market['dealingRules']['minControlledRiskStopDistance']['value'] + 1
        # Extract market Id
        marketId = market['instrument']['marketId']
        current_bid = market['snapshot']['bid']
        current_offer = market['snapshot']['offer']

        return marketId, current_bid, current_offer, limit_perc, stop_perc


    def compute_macd_from_timeseries(self, prices):
        prevBid = 0
        hist_data = []
        for p in prices['prices']:
            if p['closePrice']['bid'] is None:
                hist_data.append(prevBid)
            else:
                hist_data.append(p['closePrice']['bid'])
                prevBid = p['closePrice']['bid']
        # Calculate the MACD indicator
        px = pd.DataFrame({'close': hist_data})
        px['26_ema'] = pd.DataFrame.ewm(px['close'], span=26).mean()
        px['12_ema'] = pd.DataFrame.ewm(px['close'], span=12).mean()
        px['MACD'] = (px['12_ema'] - px['26_ema'])
        px['MACD_Signal'] = px['MACD'].rolling(9).mean()
        px['MACD_Hist'] = (px['MACD'] - px['MACD_Signal'])
        return px


    def get_dataframe_from_historic_prices(self, marketId, epic_id):
        if self.use_av_api:
            px = self.AV.macdext(marketId, AVIntervals.DAILY)
            if px is None:
                return None
            px.index = range(len(px))
        else:
            prices = self.broker.get_prices(epic_id, 'DAY', 26)
            if prices is None:
                return None
            px = self.compute_macd_from_timeseries(prices)
        return px


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
