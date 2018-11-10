import logging
import json

from Interfaces.IGInterface import IGInterface
from Interfaces.AVInterface import AVInterface
from Strategies.SimpleMACD import SimpleMACD

class StocksAutoTrader:
    """
    Class that initialise and hold references of main components like the
    broker interface, the strategy or the epic_ids list
    """
    def __init__(self, config):
        self.read_configuration(config)
        # Create IG interface
        self.IG = IGInterface(config)
        # Define the strategy to use here
        self.strategy = SimpleMACD(config)

    def read_configuration(self, config):
        """
        Read the configuration from the config json
        """
        self.epic_ids_filepath = config['general']['epic_ids_filepath']
        self.credentials_filepath = config['general']['credentials_filepath']

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
        Reads the user credentials authenticating the broker interface, builds
        the epic list and start the strategy
        """
        # Read credentials file
        try:
            with open(self.credentials_filepath, 'r') as file:
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
