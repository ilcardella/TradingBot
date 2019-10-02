import os
import sys
import inspect
import pytest
import json

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, "{}/src".format(parentdir))

from Components.MarketProvider import MarketProvider
from Components.Broker import Broker
from Components.IGInterface import IGInterface
from Components.AVInterface import AVInterface
from common.MockRequests import (
    ig_request_login,
    ig_request_set_account,
    ig_request_market_info,
    ig_request_search_market,
    ig_request_watchlist,
)


@pytest.fixture
def config():
    """
    Returns a dict with config parameter for strategy and simpleMACD
    """
    # Read configuration file
    try:
        with open("config/config.json", "r") as file:
            config = json.load(file)
    except IOError:
        exit()
    return config


@pytest.fixture
def credentials():
    """
    Returns a dict with credentials parameters
    """
    return {
        "username": "user",
        "password": "pwd",
        "api_key": "12345",
        "account_id": "12345",
        "av_api_key": "12345",
    }


@pytest.fixture
def requests(requests_mock):
    ig_request_login(requests_mock)
    ig_request_set_account(requests_mock)
    ig_request_market_info(requests_mock)
    ig_request_search_market(requests_mock)
    ig_request_watchlist(requests_mock, data="mock_watchlist_list.json")
    ig_request_watchlist(requests_mock, args="12345678", data="mock_watchlist.json")


@pytest.fixture
def make_broker(requests, config, credentials):
    # Define configuration for this test
    # config["alpha_vantage"]["enable"] = True

    # Mock services and other components
    services = {
        "ig_index": IGInterface(config, credentials),
        "alpha_vantage": AVInterface(credentials["av_api_key"], config),
    }
    broker = Broker(config, services)
    return broker


def test_market_provider_epics_list(config, make_broker):
    """
    Test the MarketProvider configured to fetch markets from an epics list
    """
    # Configure TradingBot to use an epic list
    config["general"]["market_source"]["value"] = "list"
    config["general"]["epic_ids_filepath"] = "test/test_data/epics_list.txt"

    # load test data for market info response, so it can be used to mock the info
    # for each epic in the epic_list
    mock_info = None
    try:
        with open("test/test_data/ig/mock_market_info.json", "r") as file:
            mock_info = json.load(file)
    except IOError:
        exit()

    # Create the class to test
    mp = MarketProvider(config, make_broker)

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
            with pytest.raises(StopIteration) as e:
                mp.next()
            mp.reset()
            continue
        # If we get here it means that next did not raise an exception at the end of the list
        assert False


def test_market_provider_watchlist(config, make_broker):
    """
    Test the MarketProvider configured to fetch markets from an IG watchlist
    """
    # Define configuration for this test
    config["general"]["market_source"]["value"] = "watchlist"
    # Watchlist name depending on test data json
    config["general"]["watchlist_name"] = "My Watchlist"

    # Create class to test
    mp = MarketProvider(config, make_broker)

    # The test data for market_info return always the same epic id, but the test
    # data for the watchlist contains 3 markets
    # Run the test several times resetting the market provider
    for _ in range(4):
        assert mp.next().epic == "KA.D.GSK.DAILY.IP"
        assert mp.next().epic == "KA.D.GSK.DAILY.IP"
        assert mp.next().epic == "KA.D.GSK.DAILY.IP"

        with pytest.raises(StopIteration) as e:
            mp.next()
        mp.reset()


def test_market_provider_api(config, make_broker):
    """
    Test the MarketProvider configured to fetch markets from IG nodes
    """
    # Define configuration for this test
    config["general"]["market_source"]["value"] = "api"

    # TODO
    # Create class to test
    # mp = MarketProvider(config, make_broker)
    assert True


def test_market_provider_market_from_epic(config, make_broker):
    """
    Test the MarketProvider get_market_from_epic() function
    """
    # Define configuration for this test
    config["general"]["market_source"]["value"] = "list"
    config["general"]["epic_ids_filepath"] = "test/test_data/epics_list.txt"

    # Create class to test
    mp = MarketProvider(config, make_broker)
    market = mp.get_market_from_epic("mock")
    assert market is not None
    assert market.epic == "KA.D.GSK.DAILY.IP"


def test_search_market(config, make_broker, requests_mock):
    """
    Test the MarketProvider search_market() function
    """
    # Define configuration for this test
    config["general"]["market_source"]["value"] = "list"
    config["general"]["epic_ids_filepath"] = "test/test_data/epics_list.txt"

    mp = MarketProvider(config, make_broker)

    # The mock search data contains multiple markets
    ig_request_search_market(requests_mock, data="mock_error.json")
    with pytest.raises(RuntimeError):
        market = mp.search_market("mock")
    # TODO test with single market mock data and verify no exception
