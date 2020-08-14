import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from ..components import Configuration, TradeDirection
from ..components.broker import Broker
from ..interfaces import Market, Position

DataPoints = Any
BacktestResult = Dict[str, Union[float, List[Tuple[str, TradeDirection, float]]]]
TradeSignal = Tuple[TradeDirection, Optional[float], Optional[float]]


class Strategy(ABC):
    """
    Generic strategy template to use as a parent class for custom strategies.
    """

    positions: Optional[List[Position]] = None
    broker: Broker

    def __init__(self, config: Configuration, broker: Broker) -> None:
        self.positions = None
        self.broker = broker
        # Read configuration of derived Strategy
        self.read_configuration(config)
        # Initialise derived Strategy
        self.initialise()

    def set_open_positions(self, positions: List[Position]) -> None:
        """
        Set the account open positions
        """
        self.positions = positions

    def run(self, market: Market) -> TradeSignal:
        """
        Run the strategy against the specified market
        """
        datapoints = self.fetch_datapoints(market)
        logging.debug("Strategy datapoints: {}".format(datapoints))
        if datapoints is None:
            logging.debug("Unable to fetch market datapoints")
            return TradeDirection.NONE, None, None
        return self.find_trade_signal(market, datapoints)

    #############################################################
    # OVERRIDE THESE FUNCTIONS IN STRATEGY IMPLEMENTATION
    #############################################################

    @abstractmethod
    def initialise(self) -> None:
        pass

    @abstractmethod
    def read_configuration(self, config: Configuration) -> None:
        pass

    @abstractmethod
    def fetch_datapoints(self, market: Market) -> DataPoints:
        pass

    @abstractmethod
    def find_trade_signal(self, market: Market, datapoints: DataPoints) -> TradeSignal:
        pass

    @abstractmethod
    def backtest(
        self, market: Market, start_date: datetime, end_date: datetime
    ) -> BacktestResult:
        pass
