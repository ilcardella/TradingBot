import logging
import json
from pathlib import Path
import pytz
import datetime as dt
import os

from Interfaces.IGInterface import IGInterface
from Interfaces.AVInterface import AVInterface
from Strategies.SimpleMACD import SimpleMACD

class StocksAutoTrader:
    """
    Class that initialise and hold references of main components like the
    broker interface, the strategy or the epic_ids list
    """
    def __init__(self):
        # Set timezone
        set(pytz.all_timezones_set)

        # Read configuration file
        try:
            with open('../config/config.json', 'r') as file:
                config = json.load(file)
        except IOError:
            logging.error("Configuration file not found!")
            exit()
        self.read_configuration(config)

        # Read credentials file
        try:
            with open(self.credentials_filepath, 'r') as file:
                credentials = json.load(file)
        except IOError:
            logging.error("Credentials file not found!")
            exit()

        # Define the global logging settings
        debugLevel = logging.DEBUG if self.debug_log else logging.INFO
        # If enabled define log file filename with current timestamp
        if self.enable_log:
            log_filename = self.log_file
            time_str = dt.datetime.now().isoformat()
            time_suffix = time_str.replace(':', '_').replace('.', '_')
            home = str(Path.home())
            log_filename = log_filename.replace('{timestamp}', time_suffix).replace('{home}', home)
            os.makedirs(os.path.dirname(log_filename), exist_ok=True)
            logging.basicConfig(filename=log_filename,
                            level=debugLevel,
                            format="[%(asctime)s] %(levelname)s: %(message)s")
        else:
            logging.basicConfig(level=debugLevel,
                            format="[%(asctime)s] %(levelname)s: %(message)s")

        # Create IG interface
        self.IG = IGInterface(config)
        # Init the IG interface
        if not self.IG.authenticate(credentials):
            logging.error("Authentication failed")
            exit()

        # Init AlphaVantage interface
        self.AV = AVInterface(credentials['av_api_key'])

        # Create dict of services
        services = {
            "broker": self.IG,
            "alpha_vantage": self.AV
        }

        # Define the strategy to use here
        self.strategy = SimpleMACD(config, services)

    def read_configuration(self, config):
        """
        Read the configuration from the config json
        """
        self.epic_ids_filepath = config['general']['epic_ids_filepath']
        self.credentials_filepath = config['general']['credentials_filepath']
        self.debug_log = config['general']['debug_log']
        self.enable_log = config['general']['enable_log']
        self.log_file = config['general']['log_file']

    def get_epic_ids(self):
        """
        Read a file from filesystem containing a list of epic ids.
        The filepath is defined in config.json file
        Returns a 'list' of strings where each string is a market epic
        """
        # define empty list
        epic_ids = []
        try:
            # open file and read the content in a list
            with open(self.epic_ids_filepath, 'r') as filehandle:
                filecontents = filehandle.readlines()
                for line in filecontents:
                    # remove linebreak which is the last character of the string
                    current_epic_id = line[:-1]
                    epic_ids.append(current_epic_id)
        except IOError:
            # Create the file empty
            logging.warn("Epic ids file not found, it will be created empty.")
            filehandle = open(self.epic_ids_filepath, 'w')
        logging.debug(epic_ids)
        return epic_ids

    def start(self, argv):
        """
        Read the epic ids list and start the strategy
        """
        # Read list of company epic ids and start the strategy
        self.strategy.start(self.get_epic_ids())
