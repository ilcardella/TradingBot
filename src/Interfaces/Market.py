class Market:
    """
    Represent a tradable market with latest price information
    """

    def __init__(self):
        self.epic = "unknown"
        self.id = "unknown"
        self.name = "unknown"
        self.bid = 0
        self.offer = 0
        self.high = 0
        self.low = 0
        self.stop_distance_min = 0

