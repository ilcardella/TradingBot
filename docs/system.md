# System Overview

TradingBot is a python program with the goal to automate the trading of stocks in the London Stock Exchange market.

It is designed around the idea that to trade in the stock market you need a **strategy**: a strategy is a set of rules that define the conditions where to buy, sell or hold a certain market.

TradingBot design lets the user implement a custom strategy without the trouble of developing all the boring stuff to make it work.

The following sections give an overview of the main components that compose TradingBot.

## TradingBot

TradingBot is the main entity used to initialise all the components that will be used during the main routine.

It reads the configuration file and the credentials file, it creates the configured strategy instance, the broker interface and it handles the processing of the markets with the active strategy.

## Broker Interface

TradingBot requires an interface with an executive broker in order to open and close trades in the market.

The broker interface is initialised in the `TradingBot` module and it should be independent from its underlying implementation.

At the current status, the only supported broker is IGIndex. This broker provides a very good set of API to analyse the market and manage the account. TradingBot makes also use of other 3rd party services to fetch market data such as price snapshot or technical indicators.

## Strategy

The `Strategy` is the core of the TradingBot system. It is a generic template class that can be extended with custom functions to execute trades according to the personalised strategy.

### How to use your own strategy

Anyone can create a new strategy from scratch in a few simple steps. With your own strategy you can define your own set of rules to decide whether to buy, sell or hold a specific market.

1. Setup your development environment (see `README.md`)

2. Create a new python module inside the `tradingbot/strategies` folder:

   ```bash
   cd tradingbot/strategies
   touch my_strategy.py
   ```

3. Edit the file and add a basic strategy template like the following:

   ```python
   import logging
   from typing import Tuple, Optional

   from ..components import Configuration, Interval, TradeDirection
   from ..components.broker import Broker
   from ..interfaces import Market, MarketHistory
   from . import Strategy, TradeSignal

   class MyStrategy(Strategy):
       """
       Description of the strategy
       """
       def __init__(self, config: Configuration, broker: Broker) -> None:
           super().__init__(config, broker)
           logging.info("MyStrategy initialised")

       def read_configuration(self, config: Configuration) -> None:
           # Read from the config json and store config parameters
           pass

       def initialise(self) -> None:
           # Initialise the strategy
           pass

       def fetch_datapoints(self, market: Market) -> MarketHistory:
           """
           Fetch any required datapoints (historic prices, indicators, etc.).
           The object returned by this function is passed to the 'find_trade_signal()'
           function 'datapoints' argument
           """
           # As an example, this means the strategy needs 50 data point of
           # of past prices from the 1-hour chart of the market
           return self.broker.get_prices(market, Interval.HOUR, 50)

       def find_trade_signal(self, market: Market, datapoints: MarketHistory) -> TradeSignal:
           # Here is where you want to implement your own code!
           # The market instance provide information of the market to analyse while
           # the datapoints object contains the required price datapoints
           # Returns the trade direction, limit level and stop level

           # Example:
           return TradeDirection.BUY, 150.0, 90.0
   ```

4. Add the implementation for these functions:

   * **read_configuration**: `config` is the configuration wrapper instance loaded from the configuration file
   * **initialise**: initialise the strategy or any internal members
   * **fetch_datapoints**: fetch the required past price datapoints
   * **find_trade_signal**: it is the core of your custom strategy, here you can use the broker interface to decide if trade the given epic

5. `Strategy` parent class provides a `Broker` type internal member that can be accessed with `self.broker`. This member is the TradingBot broker interface and provide functions to fetch market data, historic prices and technical indicators.

6. `Strategy` parent class provides access to another internal member that list the current open position for the configured account. Access it with `self.positions`.

7. Edit the `tradingbot/strategies/factories.py` module importing the new strategy and adding its name to the `StrategyNames` enum. Then add it to the `make` function.

8. Edit the `TradingBot` configuration file adding a new section for your strategy parameters.

9. Create a unit test for your strategy.

10. Share your strategy creating a Pull Request :)
