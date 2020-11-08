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

.. automodule:: tradingbot.components


MarketProvider
==============

.. autoclass:: MarketProvider
    :members:

Enums
-----

.. autoclass:: MarketSource
    :members:

TimeProvider
============

.. autoclass:: TimeProvider
    :members:

Enums
-----

.. autoclass:: TimeAmount
    :members:

Backtester
==========

.. autoclass:: Backtester
    :members:

Configuration
=============

.. autoclass:: Configuration
    :members:

Utils
=====

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

Broker
******

The ``Broker`` class is the wrapper of all the trading services and provides
the main interface for the ``strategies`` to access market data and perform
trades.

.. automodule:: tradingbot.components.broker

AbstractInterfaces
==================

.. autoclass:: AbstractInterface
    :members:

.. autoclass:: AccountInterface
    :members:

.. autoclass:: StocksInterface
    :members:

IGInterface
===========

.. autoclass:: IGInterface
    :members:

Enums
-----

.. autoclass:: IG_API_URL
    :members:

AVInterface
===========

.. autoclass:: AVInterface
    :members:

Enums
-----

.. autoclass:: AVInterval
    :members:

YFinanceInterface
=================

.. autoclass:: YFInterval
    :members:

Broker
======

.. autoclass:: Broker
    :members:

BrokerFactory
=============

.. autoclass:: BrokerFactory
    :members:

.. autoclass:: InterfaceNames
    :members:

Interfaces
**********

The ``Interfaces`` module contains all the interfaces used to exchange
information between different TradingBot components.
The purpose of this module is have clear internal API and avoid integration
errors.

.. automodule:: tradingbot.interfaces

Market
======

.. autoclass:: Market
    :members:

MarketHistory
=============

.. autoclass:: MarketHistory
    :members:

MarketMACD
==========

.. autoclass:: MarketMACD
    :members:

Position
========

.. autoclass:: Position
    :members:

Strategies
**********

The ``Strategies`` module contains the strategies used by TradingBot to
analyse the markets. The ``Strategy`` class is the parent from where
any custom strategy **must** inherit from.
The other modules described here are strategies available in TradingBot.

.. automodule:: tradingbot.strategies

Strategy
========

.. autoclass:: Strategy
    :members:

StrategyFactory
===============

.. autoclass:: StrategyFactory
    :members:

SimpleMACD
==========

.. autoclass:: SimpleMACD
    :members:

Weighted Average Peak Detection
===============================

.. autoclass:: WeightedAvgPeak
    :members:

Simple Bollinger Bands
======================

.. autoclass:: SimpleBollingerBands
    :members:
