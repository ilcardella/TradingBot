.. _modules:

Modules
#######

TradingBot is composed by different modules organised by their nature.
Each section of this document provide a description of the module meaning
along with the documentation of its internal members.


TradingBot
**********

.. automodule:: TradingBot

.. autoclass:: TradingBot
    :members:

Components
**********

The ``Components`` module contains the components that provides services
used by TradingBot.
The ``Broker`` class is the wrapper of all the trading services and provides
the main interface for the ``strategies`` to access market data and perform
trades.

IGInterface
===========

.. automodule:: Components.IGInterface

.. autoclass:: IGInterface
    :members:

Enums
-----

.. autoclass:: IG_API_URL
    :members:

AVInterface
===========

.. automodule:: Components.AVInterface

.. autoclass:: AVInterface
    :members:

Enums
-----

.. autoclass:: AVInterval
    :members:

Broker
======

.. automodule:: Components.Broker

.. autoclass:: Broker
    :members:

Enums
-----

.. autoclass:: Interval
    :members:

MarketProvider
==============

.. automodule:: Components.MarketProvider

.. autoclass:: MarketProvider
    :members:

Enums
-----

.. autoclass:: MarketSource
    :members:

TimeProvider
==============

.. automodule:: Components.TimeProvider

.. autoclass:: TimeProvider
    :members:

Enums
-----

.. autoclass:: TimeAmount
    :members:

Interfaces
**********

The ``Interfaces`` module contains all the interfaces used to exchange
information between different TradingBot components.
The purpose of this module is have clear internal API and avoid integration
errors.

Market
======

.. automodule:: Interfaces.Market

.. autoclass:: Market
    :members:

Strategies
**********

The ``Strategies`` module contains the strategies used by TradingBot to
analyse the markets. The ``Strategy`` class is the parent from where
any custom strategy **must** inherit from.
The other modules described here are strategies available in TradingBot.

Strategy
========

.. automodule:: Strategies.Strategy

.. autoclass:: Strategy
    :members:

StrategyFactory
===============

.. automodule:: Strategies.StrategyFactory

.. autoclass:: StrategyFactory
    :members:

SimpleMACD
==========

.. automodule:: Strategies.SimpleMACD

.. autoclass:: SimpleMACD
    :members:

Weighted Average Peak Detection
===============================

.. automodule:: Strategies.WeightedAvgPeak

.. autoclass:: WeightedAvgPeak
    :members:

Utils
*****

Common utility classes and methods

Utils
=====

.. automodule:: Utility.Utils

.. autoclass:: Utils
    :members:

Enums
=====

.. autoclass:: TradeDirection
    :members:

Exceptions
==========

.. autoclass:: MarketClosedException
    :members:

.. autoclass:: NotSafeToTradeException
    :members:
