class Strategy:
    """
    Generic strategy template to use as a parent class for custom strategies.
    Provide safety checks for new trades and handling of open positions.
    """

    def __init__(self, config, broker):
        self.positions = {}
        self.broker = broker
        # This can be overwritten in children class
        self.spin_interval = 3600
        # This must be the last operation of this function to override possible values in children class
        self.read_configuration(config)


#############################################################
# OVERRIDE THESE FUNCTIONS IN STRATEGY IMPLEMENTATION
#############################################################

    def read_configuration(self, config):
        """
        Must override
        """
        raise NotImplementedError('Not implemented: read_configuration')

    def find_trade_signal(self, epic_id):
        """
        Must override
        """
        raise NotImplementedError('Not implemented: find_trade_signal')

    def get_seconds_to_next_spin(self):
        """
        Must override
        """
        return self.spin_interval

##############################################################
##############################################################
