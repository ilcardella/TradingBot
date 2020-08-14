from typing import Any

from ..components import TradeDirection


class Position:

    deal_id: str
    size: int
    create_date: str
    direction: TradeDirection
    level: float
    limit: float
    stop: float
    currency: str
    epic: str
    market_id: str

    def __init__(self, **kargs: Any) -> None:
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
