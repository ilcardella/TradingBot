from pathlib import Path

import pytest
from common.MockRequests import (
    ig_request_login,
    ig_request_market_info,
    ig_request_search_market,
    ig_request_set_account,
    ig_request_watchlist,
)

from tradingbot.components import Configuration, MarketProvider
from tradingbot.components.broker import Broker, BrokerFactory


@pytest.fixture
def config():
    """
    Returns a dict with config parameter for strategy and simpleMACD
    """
    return Configuration.from_filepath(Path("test/test_data/trading_bot.toml"))


@pytest.fixture
def broker(requests_mock, config):
    ig_request_login(requests_mock)
    ig_request_set_account(requests_mock)
    ig_request_market_info(requests_mock)
    ig_request_search_market(requests_mock)
    ig_request_watchlist(requests_mock, data="mock_watchlist_list.json")
    ig_request_watchlist(requests_mock, args="12345678", data="mock_watchlist.json")
    return Broker(BrokerFactory(config))


def test_market_provider_epics_list(config, broker):
    """
    Test the MarketProvider configured to fetch markets from an epics list
    """
    # Configure TradingBot to use an epic list
    config.config["market_source"]["active"] = "list"
    config.config["market_source"]["epic_id_list"][
        "filepath"
    ] = "test/test_data/epics_list.txt"

    # Create the class to test
    mp = MarketProvider(config, broker)

    # Run the test several times resetting the market provider
    for _ in range(4):
        # Read the test epic list and create a local list of the expected epics
        expected_list = []
        with open("test/test_data/epics_list.txt", "r") as epics_list:
            for cnt, line in enumerate(epics_list):
                epic = line.rstrip()
                expected_list += [epic]

        # Keep caling the test function building a list of returned epics
        actual_list = []
        try:
            while True:
                actual_list.append(mp.next().epic)
        except StopIteration:
            # Verify we read all epics in the list
            assert len(expected_list) == len(actual_list)
            # Verify reading the next raise another exception
            with pytest.raises(StopIteration):
                mp.next()
            mp.reset()
            continue
        # If we get here it means that next did not raise an exception at the end of the list
        assert False


def test_market_provider_watchlist(config, broker):
    """
    Test the MarketProvider configured to fetch markets from an IG watchlist
    """
    # Define configuration for this test
    config.config["market_source"]["active"] = "watchlist"
    # Watchlist name depending on test data json
    config.config["market_source"]["watchlist"]["name"] = "My Watchlist"

    # Create class to test
    mp = MarketProvider(config, broker)

    # The test data for market_info return always the same epic id, but the test
    # data for the watchlist contains 3 markets
    # Run the test several times resetting the market provider
    for _ in range(4):
        assert mp.next().epic == "KA.D.GSK.DAILY.IP"
        assert mp.next().epic == "KA.D.GSK.DAILY.IP"
        assert mp.next().epic == "KA.D.GSK.DAILY.IP"

        with pytest.raises(StopIteration):
            mp.next()
        mp.reset()


def test_market_provider_api(config, broker):
    """
    Test the MarketProvider configured to fetch markets from IG nodes
    """
    # Define configuration for this test
    config.config["market_source"]["active"] = "api"

    # TODO
    # Create class to test
    # mp = MarketProvider(config, broker)
    assert True


def test_market_provider_market_from_epic(config, broker):
    """
    Test the MarketProvider get_market_from_epic() function
    """
    # Define configuration for this test
    config.config["market_source"]["active"] = "list"
    config.config["market_source"]["epic_id_list"][
        "filepath"
    ] = "test/test_data/epics_list.txt"

    # Create class to test
    mp = MarketProvider(config, broker)
    market = mp.get_market_from_epic("mock")
    assert market is not None
    assert market.epic == "KA.D.GSK.DAILY.IP"


def test_search_market(config, broker, requests_mock):
    """
    Test the MarketProvider search_market() function
    """
    # Define configuration for this test
    config.config["market_source"]["active"] = "list"
    config.config["market_source"]["epic_id_list"][
        "filepath"
    ] = "test/test_data/epics_list.txt"

    mp = MarketProvider(config, broker)

    # The mock search data contains multiple markets
    ig_request_search_market(requests_mock, data="mock_error.json")
    with pytest.raises(RuntimeError):
        _ = mp.search_market("mock")
    # TODO test with single market mock data and verify no exception
