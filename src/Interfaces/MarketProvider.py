import logging
import os
import inspect
import sys
from collections import deque
from enum import Enum

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from .Market import Market


class MarketSource(Enum):
    """
    Available market sources: local file list, watch list, market navigation
    through API, etc.
    """

    LIST = "list"
    WATCHLIST = "watchlist"
    API = "api"


class MarketProvider:
    """
    Provide markets from different sources based on configuration. Supports
    market lists, dynamic market exploration or watchlists
    """

    def __init__(self, config, broker):
        self.broker = broker
        self._read_configuration(config)
        self._initialise()

    def next(self):
        """
        Return the next market from the configured source
        """
        if self.market_source == MarketSource.LIST:
            return _next_from_list()
        elif self.market_source == MarketSource.WATCHLIST:
            return _next_from_list()
        elif self.market_source == MarketSource.API:
            return _next_from_api()
        else:
            raise RuntimeError("ERROR: invalid market_source configuration")

    def reset(self):
        """
        Reset internal market pointer to the beginning
        """
        logging.info("Resetting MarketProvider")
        self._initialise()

    def get_market_from_epic(self, epic):
        """
        Given a market epic id returns the related market snapshot
        """
        return self._create_market(epic)

    def _read_configuration(self, config):
        home = os.path.expanduser("~")
        self.epic_ids_filepath = config["general"]["epic_ids_filepath"].replace(
            "{home}", home
        )
        self.market_source = MarketSource(config["general"]["market_source"]["value"])
        self.watchlist_name = config["general"]["watchlist_name"]

    def _initialise(self):
        # Initialise epic list
        self.epic_list = []
        self.epic_list_iter = None
        # Initialise API members
        self.node_stack = deque()

        if self.market_source == MarketSource.LIST:
            self.epic_list = self._load_epic_ids_from_local_file(self.epic_ids_filepath)
        elif self.market_source == MarketSource.WATCHLIST:
            self.epic_list = self._load_epic_ids_from_watchlist(self.watchlist_name)
        elif self.market_source == MarketSource.API:
            self.epic_list = self._load_epic_ids_from_api_node("180500")
        else:
            raise RuntimeError("ERROR: invalid market_source configuration")
        self.epic_list_iter = iter(self.epic_list)

    def _load_epic_ids_from_local_file(self, filepath):
        """
        Read a file from filesystem containing a list of epic ids.
        The filepath is defined in config.json file
        Returns a 'list' of strings where each string is a market epic
        """
        # define empty list
        epic_ids = []
        try:
            # open file and read the content in a list
            with open(filepath, "r") as filehandle:
                filecontents = filehandle.readlines()
                for line in filecontents:
                    # remove linebreak which is the last character of the string
                    current_epic_id = line[:-1]
                    epic_ids.append(current_epic_id)
        except IOError:
            # Create the file empty
            logging.error("{} does not exist!".format(filepath))
        if len(epic_ids) < 1:
            logging.error("Epic list is empty!")
        shuffle(epic_ids)
        return epic_ids

    def _next_from_list(self):
        try:
            epic = self.epic_list_iter.next()
            return self._create_market(epic)
        except Exception as e:
            raise StopIteration

    def _load_epic_ids_from_watchlist(self, watchlist_name):
        markets = self.broker.get_markets_from_watchlist(self.watchlist_name)
        if markets is None:
            message = "Watchlist {} not found!".format(watchlist_name)
            logging.error(message)
            raise RuntimeError(message)
        return [m["epic"] for m in markets]

    def _load_epic_ids_from_api_node(self, node_id):
        node = self.broker.navigate_market_node(node_id)
        if "nodes" in node and isinstance(node["nodes"], list):
            for node in node["nodes"]:
                self.node_stack.append(node["id"])
            return self._load_epic_ids_from_api_node(self.node_stack.pop())
        if "markets" in node and isinstance(node["markets"], list):
            return [
                market["epic"]
                for market in node["markets"]
                if any(
                    [
                        "DFB" in str(market["epic"]),
                        "TODAY" in str(market["epic"]),
                        "DAILY" in str(market["epic"]),
                    ]
                )
            ]
        return []

    def _next_from_api(self):
        # Return the next item in the epic_list, but if the list is finished
        # navigate the next node in the stack and return a new list
        try:
            return self._next_from_list()
        except Exception as e:
            self.epic_list = self._load_epic_ids_from_api_node(self.node_stack.pop())
            self.epic_list_iter = iter(self.epic_list)
            return self._next_from_list()

    def _create_market(self, epic_id):
        info = self.broker.get_market_info(epic_id)
        if info is None:
            raise Exception("Unable to fetch data for {}".format(epic_id))
        market = Market()
        market.epic = info["epic"]
        market.id = info["market_id"]
        market.name = info["name"]
        market.bid = info["bid"]
        market.offer = info["offer"]
        market.high = info["high"]
        market.low = info["low"]
        return market
