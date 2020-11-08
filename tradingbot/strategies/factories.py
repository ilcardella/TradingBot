from enum import Enum
from typing import Union

from ..components import Configuration
from ..components.broker import Broker
from . import SimpleBollingerBands, SimpleMACD, WeightedAvgPeak

StrategyImpl = Union[SimpleMACD, WeightedAvgPeak, SimpleBollingerBands]


class StrategyNames(Enum):
    SIMPLE_MACD = "simple_macd"
    WEIGHTED_AVG_PEAK = "weighted_avg_peak"
    SIMPLE_BOLL_BANDS = "simple_boll_bands"


class StrategyFactory:
    """
    Factory class to create instances of Strategies. The class provide an
    interface to instantiate new objects of a given Strategy name
    """

    config: Configuration
    broker: Broker

    def __init__(self, config: Configuration, broker: Broker) -> None:
        """
        Constructor of the StrategyFactory

            - **config**: config json used to initialise Strategies
            - **broker**: instance of Broker class
              Strategies
            - Return the instance of the StrategyFactory
        """
        self.config = config
        self.broker = broker

    def make_strategy(self, strategy_name: str) -> StrategyImpl:
        """
        Create and return an instance of the Strategy class specified by
        the strategy_name

            - **strategy_name**: name of the strategy as defined in the json
              config file
            - Returns an instance of the requested Strategy or None if an
              error occurres
        """
        if strategy_name == StrategyNames.SIMPLE_MACD.value:
            return SimpleMACD(self.config, self.broker)
        elif strategy_name == StrategyNames.WEIGHTED_AVG_PEAK.value:
            return WeightedAvgPeak(self.config, self.broker)
        elif strategy_name == StrategyNames.SIMPLE_BOLL_BANDS.value:
            return SimpleBollingerBands(self.config, self.broker)
        else:
            raise ValueError("Strategy {} does not exist".format(strategy_name))

    def make_from_configuration(self) -> StrategyImpl:
        """
        Create and return an instance of the Strategy class as configured in the
        configuration file
        """
        return self.make_strategy(self.config.get_active_strategy())
