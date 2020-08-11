.. _modules:

Modules
#######

TradingBot is composed by different modules organised by their nature.
Each section of this document provide a description of the module meaning
along with the documentation of its internal members.


TradingBot
**********

.. automodule:: tradingbot

.. autoclass:: TradingBot
    :members:

Components
**********

The ``Components`` module contains the components that provides services
used by TradingBot.

Broker
======

The ``Broker`` class is the wrapper of all the trading services and provides
the main interface for the ``strategies`` to access market data and perform
trades.

AbstractInterfaces
------------------

.. automodule:: Components.Broker

.. autoclass:: AbstractInterface
    :members:

.. autoclass:: AccountInterface
    :members:

.. autoclass:: StocksInterface
    :members:

IGInterface
-----------

.. automodule:: Components.Broker

.. autoclass:: IGInterface
    :members:

Enums
^^^^^

.. autoclass:: IG_API_URL
    :members:

AVInterface
-----------

.. automodule:: Components.Broker

.. autoclass:: AVInterface
    :members:

Enums
^^^^^

.. autoclass:: AVInterval
    :members:

YFinanceInterface
-----------------

.. automodule:: Components.Broker

.. autoclass:: YFInterval
    :members:

Broker
------

.. automodule:: Components.Broker

.. autoclass:: Broker
    :members:

BrokerFactory
-------------

.. automodule:: Components.Broker

.. autoclass:: BrokerFactory
    :members:

.. autoclass:: InterfaceNames
    :members:

MarketProvider
==============

.. automodule:: Components

.. autoclass:: MarketProvider
    :members:

Enums
-----

.. autoclass:: MarketSource
    :members:

TimeProvider
============

.. automodule:: Components

.. autoclass:: TimeProvider
    :members:

Enums
-----

.. autoclass:: TimeAmount
    :members:

Backtester
==========

.. automodule:: Components

.. autoclass:: Backtester
    :members:

Configuration
=============

.. automodule:: Components

.. autoclass:: Configuration
    :members:

Utils
=====

.. automodule:: Components

.. autoclass:: Utils
    :members:

Enums
-----

.. autoclass:: TradeDirection
    :members:

.. autoclass:: Interval
    :members:

Exceptions
----------

.. autoclass:: MarketClosedException
    :members:

.. autoclass:: NotSafeToTradeException
    :members:

Interfaces
**********

The ``Interfaces`` module contains all the interfaces used to exchange
information between different TradingBot components.
The purpose of this module is have clear internal API and avoid integration
errors.

Market
======

.. automodule:: Interfaces

.. autoclass:: Market
    :members:

MarketHistory
=============

.. automodule:: Interfaces

.. autoclass:: MarketHistory
    :members:

MarketMACD
==========

.. automodule:: Interfaces

.. autoclass:: MarketMACD
    :members:

Position
========

.. automodule:: Interfaces

.. autoclass:: Position
    :members:

Strategies
**********

The ``Strategies`` module contains the strategies used by TradingBot to
analyse the markets. The ``Strategy`` class is the parent from where
any custom strategy **must** inherit from.
The other modules described here are strategies available in TradingBot.

Strategy
========

.. automodule:: Strategies

.. autoclass:: Strategy
    :members:

StrategyFactory
===============

.. automodule:: Strategies

.. autoclass:: StrategyFactory
    :members:

SimpleMACD
==========

.. automodule:: Strategies

.. autoclass:: SimpleMACD
    :members:

Weighted Average Peak Detection
===============================

.. automodule:: Strategies

.. autoclass:: WeightedAvgPeak
    :members:
