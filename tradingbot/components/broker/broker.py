from typing import Any, Dict, List, Optional

from ...interfaces import Market, MarketHistory, MarketMACD, Position
from .. import Interval, TradeDirection
from . import AccountInterface, BrokerFactory, StocksInterface


class Broker:
    """
    This class provides a template interface for all those broker related
    actions/tasks wrapping the actual implementation class internally
    """

    factory: BrokerFactory
    stocks_ifc: StocksInterface
    account_ifc: AccountInterface

    def __init__(self, factory: BrokerFactory) -> None:
        self.factory = factory
        self.stocks_ifc = self.factory.make_stock_interface_from_config()
        self.account_ifc = self.factory.make_account_interface_from_config()

    def get_open_positions(self) -> List[Position]:
        """
        Returns the current open positions
        """
        return self.account_ifc.get_open_positions()

    def get_markets_from_watchlist(self, watchlist_name: str) -> List[Market]:
        """
        Return a name list of the markets in the required watchlist
        """
        return self.account_ifc.get_markets_from_watchlist(watchlist_name)

    def navigate_market_node(self, node_id: str) -> Dict[str, Any]:
        """
        Return the children nodes of the requested node
        """
        return self.account_ifc.navigate_market_node(node_id)

    def get_account_used_perc(self) -> Optional[float]:
        """
        Returns the account used value in percentage
        """
        return self.account_ifc.get_account_used_perc()

    def close_all_positions(self) -> bool:
        """
        Attempt to close all the current open positions
        """
        return self.account_ifc.close_all_positions()

    def close_position(self, position: Position) -> bool:
        """
        Attempt to close the requested open position
        """
        return self.account_ifc.close_position(position)

    def trade(
        self, market_id: str, trade_direction: TradeDirection, limit: float, stop: float
    ):
        """
        Request a trade of the given market
        """
        return self.account_ifc.trade(market_id, trade_direction, limit, stop)

    def get_market_info(self, market_id: str) -> Market:
        """
        Return the last available snapshot of the requested market
        """
        return self.account_ifc.get_market_info(market_id)

    def search_market(self, search: str) -> List[Market]:
        """
        Search for a market from a search string
        """
        return self.account_ifc.search_market(search)

    def get_macd(
        self, market: Market, interval: Interval, datapoints_range: int
    ) -> MarketMACD:
        """
        Return a pandas dataframe containing MACD technical indicator
        for the requested market with requested interval
        """
        return self.stocks_ifc.get_macd(market, interval, datapoints_range)

    def get_prices(
        self, market: Market, interval: Interval, data_range: int
    ) -> MarketHistory:
        """
        Returns past prices for the given market

            - market: market to query prices for
            - interval: resolution of the time series: minute, hours, etc.
            - data_range: amount of past datapoint to fetch
            - Returns the MarketHistory instance
        """
        return self.stocks_ifc.get_prices(market, interval, data_range)
