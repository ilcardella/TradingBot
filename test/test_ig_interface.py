import os
import sys
import inspect
import pytest
import json

currentdir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, '{}/scripts'.format(parentdir))

from Interfaces.IGInterface import IGInterface


@pytest.fixture
def config():
    """
    Returns a dict with config parameter for ig_interface
    """
    return {
        "ig_interface": {
            "order_type": "MARKET",
            "order_size": 1,
            "order_expiry": "DFB",
            "order_currency": "GBP",
            "order_force_open": True,
            "use_g_stop": True,
            "use_demo_account": True,
            "controlled_risk": True,
            "paper_trading": False
        }
    }


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
        "av_api_key": "12345"
    }


@pytest.fixture
def ig(config):
    """
    Returns a instance of IGInterface
    """
    return IGInterface(config)


def read_json(filepath):
    # Read mock file
    try:
        with open(filepath, 'r') as file:
            return json.load(file)
    except IOError:
        exit()


def test_init(ig, config):
    assert ig.orderType == config['ig_interface']['order_type']
    assert ig.orderSize == config['ig_interface']['order_size']
    assert ig.orderExpiry == config['ig_interface']['order_expiry']
    assert ig.orderCurrency == config['ig_interface']['order_currency']
    assert ig.orderForceOpen == config['ig_interface']['order_force_open']
    assert ig.useGStop == config['ig_interface']['use_g_stop']
    assert ig.useDemo == config['ig_interface']['use_demo_account']
    assert ig.paperTrading == config['ig_interface']['paper_trading']


def test_authenticate(ig, credentials, requests_mock):
    # Define mock requests
    mock_headers = {
        'CST': 'mock',
        'X-SECURITY-TOKEN': 'mock'
    }
    data = read_json('test/test_data/mock_ig_login.json')
    requests_mock.post(ig.apiBaseURL+'/session',
                       json=data, headers=mock_headers)
    data = read_json('test/test_data/mock_ig_set_account.json')
    requests_mock.put(ig.apiBaseURL+'/session', json=data)

    # Call function to test
    result = ig.authenticate(credentials)

    # Assert results
    assert ig.authenticated_headers['CST'] == mock_headers['CST']
    assert ig.authenticated_headers['X-SECURITY-TOKEN'] == mock_headers['X-SECURITY-TOKEN']
    assert result == True


def test_authenticate_fail(ig, credentials, requests_mock):
    # Define mock requests
    mock_headers = {
        'CST': 'mock',
        'X-SECURITY-TOKEN': 'mock'
    }
    data = {
        "errorCode": "error.security.invalid-details"
    }
    requests_mock.post(ig.apiBaseURL+'/session', text='Fail',
                       status_code=401, headers=mock_headers)
    data = read_json('test/test_data/mock_ig_set_account.json')
    requests_mock.put(ig.apiBaseURL+'/session', text='Success')

    # Call function to test
    result = ig.authenticate(credentials)

    # Assert results
    assert result == False


def test_set_default_account(ig, credentials, requests_mock):
    data = read_json('test/test_data/mock_ig_set_account.json')
    requests_mock.put(ig.apiBaseURL+'/session', status_code=200, json=data)

    result = ig.set_default_account(credentials['account_id'])

    assert result == True


def test_set_default_account_fail(ig, credentials, requests_mock):
    requests_mock.put(ig.apiBaseURL+'/session',
                      status_code=403, text='Success')

    result = ig.set_default_account(credentials['account_id'])

    assert result == False


def test_get_account_balance(ig, requests_mock):
    data = read_json('test/test_data/mock_ig_account_details.json')
    requests_mock.put(ig.apiBaseURL+'/session', status_code=200, json=data)
    balance, deposit = ig.get_account_balance()

    assert balance is not None
    assert deposit is not None
    assert balace == 16093.12
    assert deposit == 0.0
