import logging
import json

from IGInterface import IGInterface
from AVInterface import AVInterface
from Strategies.SimpleMACD import SimpleMACD

class StocksAutoTrader:
    def __init__(self, config):
        self.read_configuration(config)
        # Create IG interface
        self.IG = IGInterface(config)
        # Define the strategy to use here
        self.strategy = SimpleMACD(config)

    def read_configuration(self, config):
        self.epic_ids_filepath = config['general']['epic_ids_filepath']

    def get_epic_ids(self):
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
        # Read credentials file
        try:
            with open('../config/.credentials', 'r') as file:
                credentials = json.load(file)
        except IOError:
            logging.error("Credentials file not found!")
            return

        # Init the broker interface
        if not self.IG.authenticate(credentials):
            logging.warn("Authentication failed")
            return

        # Init AlphaVantage interface
        AV = AVInterface(credentials['av_api_key'])

        # Read list of company epic ids
        main_epic_ids = self.get_epic_ids()

        self.strategy.start(self.IG, main_epic_ids)
