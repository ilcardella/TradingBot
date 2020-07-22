class Market:
    """
    Represent a tradable market with latest price information
    """

    epic: str = "unknown"
    id: str = "unknown"
    name: str = "unknown"
    bid: float = 0.0
    offer: float = 0.0
    high: float = 0.0
    low: float = 0.0
    stop_distance_min: float = 0.0
    expiry: str = "unknown"

    def __init__(self) -> None:
        pass
