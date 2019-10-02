System Overview
###############

TradingBot is a python program with the goal to automate the trading
of stocks in the London Stock Exchange market.
It is designed around the idea that to trade in the stock market
you need a **strategy**: a strategy is a set of rules that define the
conditions where to buy, sell or hold a certain market.
TradingBot design lets the user implement a custom strategy
without the trouble of developing all the boring stuff to make it work.

The following sections give an overview of the main components that compose
TradingBot.

TradingBot
**********

TradingBot is the main entiy used to initialised all the
components that will be used during the main routine.
It reads the configuration file and the credentials file, it creates the
configured strategy instance, the broker interface and it handle the
processing of the markets with the active strategy.

Broker interface
****************

TradingBot requires an interface with an executive broker in order to open
and close trades in the market.
The broker interface is initialised in the ``TradingBot`` module and
it should be independent from its underlying implementation.

At the current status, the only supported broker is IGIndex. This broker
provides a very good set of API to analyse the market and manage the account.
TradingBot makes also use of other 3rd party services to fetch market data such
as price snapshot or technical indicators.

Strategy
********

The ``Strategy`` is the core of the TradingBot system.
It is a generic template class that can be extended with custom functions to
execute trades according to the personalised strategy.

How to use your own strategy
============================

Anyone can create a new strategy from scratch in a few simple steps.
With your own strategy you can define your own set of rules
to decide whether to buy, sell or hold a specific market.

#. Setup your development environment (see :ref:`readme`)

#. Create a new python module inside the Strategy folder :

   .. code-block:: shell

    cd Strategies
    touch my_strategy.py

#. Edit the file and add a basic strategy template like the following:

   .. code-block:: python

    import os
    import inspect
    import sys
    import logging

    # Required for correct import path
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)
    sys.path.insert(0,parentdir)

    from Components.Broker import Interval
    from .Strategy import Strategy
    from Utility.Utils import Utils, TradeDirection
    # Import any other required module

    class my_strategy(Strategy): # Extends Strategy module
        """
        Description of the strategy
        """
        def read_configuration(self, config):
            # Read from the config json and store config parameters
            pass

        def initialise(self):
            # Initialise the strategy
            pass

        def fetch_datapoints(self, market):
            """
            Fetch any required datapoints (historic prices, indicators, etc.).
            The object returned by this function is passed to the 'find_trade_signal()'
            function 'datapoints' argument
            """
            # As an example, this means the strategy needs 50 data point of
            # of past prices from the 1-hour chart of the market
            return self.broker.get_prices(market.epic, Interval.HOUR, 50)

        def find_trade_signal(self, market, prices):
            # Here is where you want to implement your own code!
            # The market instance provide information of the market to analyse while
            # the prices dictionary contains the required price datapoints
            # Returns the trade direction, stop level and limit level
            # As an examle:
            return TradeDirection.BUY, 90, 150

        def get_seconds_to_next_spin(self):
            # Return the amount of seconds between each spin of the strategy
            # Each spin analyses all the markets in a list/watchlist
            # Some strategies might require to run once a day, while other might
            # need to run continuosly, here you can make your decision

#. Add the implementation for these functions:

   * *read_configuration*: ``config`` is the json object loaded from the ``config.json`` file
   * *initialise*: initialise the strategy or any internal members
   * *fetch_datapoints*: fetch the required past price datapoints
   * *find_trade_signal*: it is the core of your custom strategy, here you can use the broker interface to decide if trade the given epic
   * *get_seconds_to_next_spin*: the *find_trade_signal* is called for every epic requested. After that TradingBot will wait for the amount of seconds defined in this function

#. ``Strategy`` parent class provides a ``Broker`` type internal member that
   can be accessed with ``self.broker``. This member is the TradingBot broker
   interface and provide functions to fetch market data, historic prices and
   technical indicators. See the :ref:`modules` section for more details.

#. ``Strategy`` parent class provides access to another internal member that
   list the current open position for the configured account. Access it with
   ``self.positions``.

#. Edit the ``StrategyFactory`` module inporting the new strategy and adding
   its name to the ``StrategyNames`` enum. Then add it to the *make* function

   .. code-block:: python
      :lineno-start: 28

        def make_strategy(self, strategy_name):
            if strategy_name == StrategyNames.SIMPLE_MACD.value:
                return SimpleMACD(self.config, self.broker)
            elif strategy_name == StrategyNames.FAIG.value:
                return FAIG_iqr(self.config, self.broker)
            elif strategy.name == StrateyNames.MY_STRATEGY.value:
                return MY_STRATEGY(self.config, self.broker)
            else:
                logging.error('Impossible to create strategy {}. It does not exist'.format(strategy_name))

#. Edit the ``config.json`` adding a new section for your strategy parameters

#. Create a unit test for your strategy

#. Share your strategy creating a Pull Request :)
