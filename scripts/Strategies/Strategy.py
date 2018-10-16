import logging

class Strategy:
    def __init__(self, config):
        # Define common settings in strategies
        self.order_size = config['ig_interface']['order_size']
        self.max_account_usable = config['general']['max_account_usable']
        self.read_configuration(config)

    def spin(self, broker, epic_ids):
        logging.error("Strategy not defined!")

    def read_configuration(self, config):
        raise NotImplementedError('Not implemented')
