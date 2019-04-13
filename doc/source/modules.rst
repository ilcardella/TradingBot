.. _modules:

Modules
=======

TradingBot is composed by different modules organised by their nature.
Each section of this document provide a description of the module meaning
along with the documentation of its internal members.


TradingBot
^^^^^^^^^^

.. automodule:: TradingBot

.. autoclass:: TradingBot
    :members:

Interfaces
^^^^^^^^^^

The ``Interfaces`` module contains all those interfaces with external
services used by TradingBot.
The ``Broker`` class is the wrapper of all the trading services and provides
the main interface for the ``strategies`` to access market data and perform
trades.

IGInterface
"""""""""""

.. automodule:: Interfaces.IGInterface

.. autoclass:: IGInterface
    :members:

AVInterface
"""""""""""

.. automodule:: Interfaces.AVInterface

.. autoclass:: AVInterface
    :members:

Broker
""""""

.. automodule:: Interfaces.Broker

.. autoclass:: Broker
    :members:


Strategies
^^^^^^^^^^

The ``Strategies`` module contains the strategies used by TradingBot to
analyse the markets. The ``Strategy`` class is the parent from where
any custom strategy **must** inherit from.
The other modules described here are strategies available in TradingBot.

Strategy
""""""""

.. automodule:: Strategies.Strategy

.. autoclass:: Strategy
    :members:

StrategyFactory
"""""""""""""""

.. automodule:: Strategies.StrategyFactory

.. autoclass:: StrategyFactory
    :members:

SimpleMACD
""""""""""

.. automodule:: Strategies.SimpleMACD

.. autoclass:: SimpleMACD
    :members:

Weighted Average Peak Detection
"""""""""""""""""""""""""""""""

.. automodule:: Strategies.WeightedAvgPeak

.. autoclass:: WeightedAvgPeak
    :members:

Utils
^^^^^

.. automodule:: Utils

.. autoclass:: Utils
    :members:
