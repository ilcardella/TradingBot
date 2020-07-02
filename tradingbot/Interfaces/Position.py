class Position:
    def __init__(self, **kargs):
        self.deal_id = kargs["deal_id"]
        self.size = kargs["size"]
        self.create_date = kargs["create_date"]
        self.direction = kargs["direction"]
        self.level = kargs["level"]
        self.limit = kargs["limit"]
        self.stop = kargs["stop"]
        self.currency = kargs["currency"]
        self.epic = kargs["epic"]
        self.market_id = kargs["market_id"]
