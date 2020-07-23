import logging
from datetime import datetime
from typing import Optional

from tradingbot.Components.Broker.Broker import Broker
from tradingbot.Interfaces.Market import Market
from tradingbot.Strategies.Strategy import BacktestResult
from tradingbot.Strategies.StrategyFactory import StrategyImpl


class Backtester:
    """
    Provides capability to backtest markets on a defined range of time
    """

    broker: Broker
    strategy: StrategyImpl
    result: Optional[BacktestResult]

    def __init__(self, broker: Broker, strategy: StrategyImpl) -> None:
        logging.info("Backtester created")
        self.broker = broker
        self.strategy = strategy
        self.result = None

    def start(self, market: Market, start_dt: datetime, end_dt: datetime) -> None:
        """Backtest the given market within the specified range
        """
        logging.info(
            "Backtester started for market id {} from {} to {}".format(
                market.id, start_dt.date(), end_dt.date()
            )
        )
        self.result = self.strategy.backtest(market, start_dt, end_dt)

    def print_results(self) -> None:
        """Print backtest result in log file
        """
        logging.info("Backtest result:")
        logging.info(self.result)
