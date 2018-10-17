import requests
import json
import logging
import time

from Utils import *

class IGInterface():
    def __init__(self, config):
        self.read_configuration(config)
        demoPrefix = 'demo-' if self.useDemo else ''
        self.apiBaseURL = 'https://' + demoPrefix + 'api.ig.com/gateway/deal'
        self.authenticated_headers = ''

    def read_configuration(self, config):
        self.useDemo = config['ig_interface']['use_demo_account']
        self.orderType = config['ig_interface']['order_type']
        self.orderSize = config['ig_interface']['order_size']
        self.orderExpiry = config['ig_interface']['order_expiry']
        self.useGStop = config['ig_interface']['use_g_stop']
        self.orderCurrency = config['ig_interface']['order_currency']
        self.orderForceOpen = config['ig_interface']['order_force_open']

    def authenticate(self, credentials):
        data = {"identifier": credentials['username'], "password": credentials['password']}
        headers = {'Content-Type': 'application/json; charset=utf-8',
                        'Accept': 'application/json; charset=utf-8',
                        'X-IG-API-KEY': credentials['api_key'],
                        'Version': '2'
                        }
        url = self.apiBaseURL + '/session'
        response = requests.post(url,
                                data=json.dumps(data),
                                headers=headers)
        headers_json = dict(response.headers)
        try:
            CST_token = headers_json["CST"]
            x_sec_token = headers_json["X-SECURITY-TOKEN"]
        except:
            return False

        self.authenticated_headers = {'Content-Type': 'application/json; charset=utf-8',
                                'Accept': 'application/json; charset=utf-8',
                                'X-IG-API-KEY': credentials['api_key'],
                                'CST': CST_token,
                                'X-SECURITY-TOKEN': x_sec_token}

        self.set_default_account(credentials['account_id'])
        return True

    def set_default_account(self, accountId):
        url = self.apiBaseURL + '/session'
        data = {"accountId": accountId, "defaultAccount": "True"}
        auth_r = requests.put(url,
                            data=json.dumps(data),
                            headers=self.authenticated_headers)
        logging.info('Using default account: {}'.format(accountId))
        return True

    def get_account_balances(self):
        base_url = self.apiBaseURL + "/accounts"
        d = self.http_get(base_url)
        if d is not None:
            for i in d['accounts']:
                if str(i['accountType']) == "SPREADBET":
                    balance = i['balance']['balance']
                    deposit = i['balance']['deposit']
                    return balance, deposit
        else:
            return None, None

    def get_open_positions(self):
        positionMap = {}
        base_url = self.apiBaseURL + "/positions"
        position_json = self.http_get(base_url)
        if position_json is not None:
            for item in position_json['positions']:
                direction = item['position']['direction']
                dealSize = item['position']['dealSize']
                ccypair = item['market']['epic']
                key = ccypair + '-' + direction
                if(key in positionMap):
                    positionMap[key] = dealSize + positionMap[key]
                else:
                    positionMap[key] = dealSize
            return positionMap
        else:
            return None


    def get_market_info(self, epic_id):
        base_url = self.apiBaseURL + '/markets/' + str(epic_id)
        market = self.http_get(base_url)
        return market if market is not None else None


    def get_prices(self, epic_id, resolution, range):
        # Price resolution (MINUTE, MINUTE_2, MINUTE_3, MINUTE_5,
        # MINUTE_10, MINUTE_15, MINUTE_30, HOUR, HOUR_2, HOUR_3,
        # HOUR_4, DAY, WEEK, MONTH)
        base_url = self.apiBaseURL + "/prices/" + str(epic_id) + "/" + str(resolution) + "/" + str(range)
        d = self.http_get(base_url)
        if d is not None and 'allowance' in d:
            remaining_allowance = d['allowance']['remainingAllowance']
            reset_time = humanize_time(int(d['allowance']['allowanceExpiry']))
            if remaining_allowance < 50:
                logging.warn("Remaining API calls left: {}".format(str(remaining_allowance)))
                logging.warn("Time to API Key reset: {}".format(str(reset_time)))
        return d if d is not None else None


    def trade(self, epic_id, trade_direction, limit, stop):
        base_url = self.apiBaseURL + '/positions/otc'
        data = {
            "direction": trade_direction,
            "epic": epic_id,
            "limitLevel": limit,
            "orderType": self.orderType,
            "size": self.orderSize,
            "expiry": self.orderExpiry,
            "guaranteedStop": self.useGStop,
            "currencyCode": self.orderCurrency,
            "forceOpen": self.orderForceOpen,
            "stopLevel": stop
        }

        r = requests.post(
            base_url,
            data=json.dumps(data),
            headers=self.authenticated_headers)

        logging.debug(r.status_code)
        logging.debug(r.reason)
        logging.debug(r.text)

        d = json.loads(r.text)
        deal_ref = d['dealReference']
        time.sleep(1)

        # Confirm market order
        base_url = self.apiBaseURL + '/confirms/' + deal_ref
        d = self.http_get(base_url)
        if d is not None:
            DEAL_ID = d['dealId']
            logging.debug(d)
            logging.info("Deal id {} has status {} with reason {}".format(str(DEAL_ID),
                                                                            d['dealStatus'],
                                                                            d['reason']))
            if str(d['reason']) != "SUCCESS":
                logging.warn("Trade {} of {} has failed!".format(trade_direction,epic_id))
                time.sleep(1)
                return False
            else:
                logging.info("Order {} for {} opened with limit={} and stop={}".format(trade_direction,
                            epic_id, limit, stop))
                time.sleep(1)
                return True
        return False

    def http_get(self, url):
        auth_r = requests.get(url, headers=self.authenticated_headers)
        logging.debug(auth_r.status_code)
        logging.debug(auth_r.reason)
        logging.debug(auth_r.text)
        d = json.loads(auth_r.text)
        if 'errorCode' in d:
            return None
        else:
            return d
