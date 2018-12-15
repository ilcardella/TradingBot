System Overview
===============

TradingBot is a python script with the goal to automate the trading
of stocks in the London Stock Exchange market.
It is designed around the idea that to trade in the stock market
you need a **strategy**: a strategy is a set of rules that define the
conditions where to buy, sell or hold a certain market.
TradingBot design lets the user implement a custom strategy
without the trouble of developing all the boring stuff to make it work.

The following sections give an overview of the main components that compose
TradingBot.

TradingBot
""""""""""

TradingBot is the main component used to initialised all the other
components that will be used during the main routine.
It instantiate a strategy and the broker interface reading the provided
user credentials.

Broker interface
""""""""""""""""

TradingBot requires an interface with an executive broker in order to open
and close trades in the market.
The broker interface is initialised in the ``TradingBot`` module and
it should be independent from its underlying implementation.

At the current status, the only supported broker is IGIndex. This broker
provides a very good set of API to analyse the market and manage the account.

Strategy
""""""""

The ``Strategy`` is the core of the TradingBot system. It wraps the custom
implementation and handles the open positions, the margin limits and the trades
themselves.
It is a generic class that can be extended with custom functions to execute
trades according to the personalised strategy.

How to use your own strategy
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Anyone can create a new strategy from scratch defining its own set of rules
to decide whether to buy, sell or hold a specific market.
To do that follow this steps:

#. Create a new python module inside the Strategy folder :

   .. code-block:: shell

    cd Strategies
    touch my_strategy.py

#. Edit the file and add a basic strategy template like the following:

   .. code-block:: python

    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)
    sys.path.insert(0,parentdir)

    from .Strategy import Strategy
    from Utils import Utils, TradeDirection

    class my_strategy(Strategy): # Extends Strategy module
       def __init__(self, config):
           super().__init__(config) # Call parent constructor

       def read_configuration(self, config):
           # Read from the config json and store config parameters

       def find_trade_signal(self, broker, epic_id):
           # Given a broker interface and an IG epic decide the trade direction
           # return TradeDirection.XXX, stop_level, limit_level

       def get_seconds_to_next_spin(self):
           # Return the amount of seconds between each spin of the strategy

#. Add the implementation for those function:

   * *read_configuration*: ``config`` is the json object loaded from the ``config.json`` file
   * *find_trade_signal*: it is the core of your custom strategy, here you can use the broker interface to decide if trade the given epic
   * *get_seconds_to_next_spin*: the *find_trade_signal* is called for every epic defined in the ``epic_ids.txt`` file. After that TradingBot will wait for the amount of seconds defined in this function

#. Edit the ``TradingBot`` module initialising the new strategy

   .. code-block:: python
      :lineno-start: 13

      # Define the strategy to use here
      self.strategy = my_strategy(config)

#. Edit the ``config.json`` adding a new section for your strategy parameters
#. Share your strategy and create a Pull Request in GitHub :)
