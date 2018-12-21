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
Ideally these interfaces should be completely independent and reusable.

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

FAIG
""""

.. automodule:: Strategies.FAIG_iqr

.. autoclass:: FAIG_iqr
    :members:

Utils
^^^^^

.. automodule:: Utils

.. autoclass:: Utils
    :members:
