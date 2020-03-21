from abc import ABC, abstractmethod


class AccountInterface(ABC):
    @abstractmethod
    def __init__(self, config):
        pass

    @abstractmethod
    def authenticate(self):
        pass

    @abstractmethod
    def set_default_account(self, account_id):
        pass

    @abstractmethod
    def get_account_balances(self):
        pass

    @abstractmethod
    def get_open_positions(self):
        pass

    @abstractmethod
    def get_positions_map(self):
        pass

    @abstractmethod
    def get_market_info(self, market_ticker):
        pass

    @abstractmethod
    def search_market(self, search_string):
        pass

    @abstractmethod
    def trade(self, ticker, direction, limit, stop):
        pass

    @abstractmethod
    def close_position(self, position):
        pass

    @abstractmethod
    def close_all_positions(self):
        pass

    @abstractmethod
    def get_account_used_perc(self):
        pass

    @abstractmethod
    def get_markets_from_watchlist(self, watchlist_id):
        pass


class StocksInterface(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def get_prices(self, market_ticker, interval, data_range):
        pass

    @abstractmethod
    def get_macd(self, market_ticker, interval, data_range):
        pass
