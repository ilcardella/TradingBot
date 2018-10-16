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
        self.accountId = config['ig_interface']['account_id']
        self.orderType = config['ig_interface']['order_type']
        self.orderSize = config['ig_interface']['order_size']
        self.orderExpiry = config['ig_interface']['order_expiry']
        self.useGStop = config['ig_interface']['use_g_stop']
        self.orderCurrency = config['ig_interface']['order_currency']
        self.orderForceOpen = config['ig_interface']['order_force_open']
        self.apiKey = config['ig_interface']['api_key']

    def authenticate(self, username, password):
        credentials = {"identifier": username, "password": password}
        headers = {'Content-Type': 'application/json; charset=utf-8',
                        'Accept': 'application/json; charset=utf-8',
                        'X-IG-API-KEY': self.apiKey,
                        'Version': '2'
                        }
        url = self.apiBaseURL + '/session'
        response = requests.post(url,
                                data=json.dumps(credentials),
                                headers=headers)
        headers_json = dict(response.headers)
        try:
            CST_token = headers_json["CST"]
            x_sec_token = headers_json["X-SECURITY-TOKEN"]
        except:
            logging.warn("Authentication failed")
            return False

        logging.debug(R"CST: {}".format(CST_token))
        logging.debug(R"X-SECURITY-TOKEN: {}".format(x_sec_token))
        self.authenticated_headers = {'Content-Type': 'application/json; charset=utf-8',
                                'Accept': 'application/json; charset=utf-8',
                                'X-IG-API-KEY': self.apiKey,
                                'CST': CST_token,
                                'X-SECURITY-TOKEN': x_sec_token}

        self.set_default_account(self.accountId)
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
        auth_r = requests.get(base_url, headers=self.authenticated_headers)
        d = json.loads(auth_r.text)

        logging.debug(auth_r.status_code)
        logging.debug(auth_r.reason)
        logging.debug(auth_r.text)

        for i in d['accounts']:
            if str(i['accountType']) == "SPREADBET":
                balance = i['balance']['balance']
                deposit = i['balance']['deposit']
                return balance, deposit

    def get_open_positions(self):
        positionMap = {}
        position_base_url = self.apiBaseURL + "/positions"
        position_auth_r = requests.get(position_base_url,
                                        headers=self.authenticated_headers)
        position_json = json.loads(position_auth_r.text)

        logging.debug(position_auth_r.status_code)
        logging.debug(position_auth_r.reason)
        logging.debug(position_auth_r.text)

        for item in position_json['positions']:
            direction = item['position']['direction']
            dealSize = item['position']['dealSize']
            ccypair = item['market']['epic']
            key = ccypair + '-' + direction
            if(key in positionMap):
                positionMap[key] = dealSize + positionMap[key]
            else:
                positionMap[key] = dealSize
        logging.debug("Current position summary: {}".format(positionMap))
        return positionMap


    def get_market_info(self, epic_id):
        base_url = self.apiBaseURL + '/markets/' + str(epic_id)
        auth_r = requests.get(base_url, headers=self.authenticated_headers)
        return json.loads(auth_r.text)


    def get_prices(self, epic_id, resolution, range):
        # Price resolution (MINUTE, MINUTE_2, MINUTE_3, MINUTE_5,
        # MINUTE_10, MINUTE_15, MINUTE_30, HOUR, HOUR_2, HOUR_3,
        # HOUR_4, DAY, WEEK, MONTH)
        base_url = self.apiBaseURL + "/prices/" + str(epic_id) + "/" + str(resolution) + "/" + str(range)
        auth_r = requests.get(base_url, headers=self.authenticated_headers)
        d = json.loads(auth_r.text)
        logging.debug(auth_r.status_code)
        logging.debug(auth_r.reason)
        logging.debug(auth_r.text)

        if 'allowance' in d:
            remaining_allowance = d['allowance']['remainingAllowance']
            reset_time = humanize_time(int(d['allowance']['allowanceExpiry']))
            logging.debug("Remaining API calls left: {}".format(str(remaining_allowance)))
            logging.debug("Time to API Key reset: {}".format(str(reset_time)))
        return d

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
        auth_r = requests.get(base_url, headers=self.authenticated_headers)
        d = json.loads(auth_r.text)
        DEAL_ID = d['dealId']
        logging.debug(d)
        logging.info("Deal id {} has status {} with reason {}".format(str(DEAL_ID),
                                                                        d['dealStatus'],
                                                                        d['reason']))
        if str(d['reason']) != "SUCCESS":
            logging.warn("Trade {} of {} has failed!".format(trade_direction,epic_id))
            time.sleep(1)
        else:
            logging.info("Order {} for {} opened with limit={} and stop={}".format(trade_direction,
                        epic_id, limit, stop))
            time.sleep(1)

    def humanize_time(self, secs):
        mins, secs = divmod(secs, 60)
        hours, mins = divmod(mins, 60)
        return '%02d:%02d:%02d' % (hours, mins, secs)
