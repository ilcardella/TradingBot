from typing import List, Optional

from pydantic import BaseModel, Field


class LoggingConfig(BaseModel):
    enable: bool = True
    log_filepath: str = "{home}/.TradingBot/log/trading_bot_{timestamp}.log"
    debug: bool = False


class EpicIdListConfig(BaseModel):
    filepath: str = ""


class WatchlistConfig(BaseModel):
    name: str = ""


class MarketSourceConfig(BaseModel):
    active: str = "list"
    values: List[str] = []
    epic_id_list: Optional[EpicIdListConfig] = None
    watchlist: Optional[WatchlistConfig] = None


class IGInterfaceConfig(BaseModel):
    order_type: str = "MARKET"
    order_size: float = 1
    order_expiry: str = "DFB"
    order_currency: str = "GBP"
    order_force_open: bool = True
    use_g_stop: bool = False
    use_demo_account: bool = True
    controlled_risk: bool = False
    api_timeout: float = 3.0


class AlphaVantageConfig(BaseModel):
    api_timeout: float = 12.0


class YFinanceConfig(BaseModel):
    api_timeout: float = 0.5


class StocksInterfaceConfig(BaseModel):
    active: str = "ig_interface"
    values: List[str] = []
    ig_interface: Optional[IGInterfaceConfig] = None
    alpha_vantage: Optional[AlphaVantageConfig] = None
    yfinance: Optional[YFinanceConfig] = None


class AccountInterfaceConfig(BaseModel):
    active: str = "ig_interface"
    values: List[str] = []


class SimpleMACDConfig(BaseModel):
    max_spread_perc: float = 5.0
    limit_perc: float = 10.0
    stop_perc: float = 5.0


class WeightedAvgPeakConfig(BaseModel):
    max_spread: float = 3.0
    limit_perc: float = 10.0
    stop_perc: float = 5.0


class SimpleBollingerBandsConfig(BaseModel):
    window: int = 60
    limit_perc: float = 10.0
    stop_perc: float = 5.0


class VolumeProfileConfig(BaseModel):
    max_spread_perc: float = 0.1
    lookback_periods: int = 50
    value_area_percentage: float = 70
    price_bins: int = 30
    imbalance_threshold: float = 1.5
    atr_period: int = 14
    base_atr_multiplier: float = 1.5
    min_risk_reward: float = 1.5
    max_risk_reward: float = 3.0


class StrategiesConfig(BaseModel):
    active: str = "simple_macd"
    values: List[str] = []
    simple_macd: Optional[SimpleMACDConfig] = None
    simple_boll_bands: Optional[SimpleBollingerBandsConfig] = None
    volume_profile: Optional[VolumeProfileConfig] = None


class TradingBotConfig(BaseModel):
    max_account_usable: float = 50.0
    time_zone: str = "UTC"
    credentials_filepath: str = ""
    spin_interval: int = 3600
    paper_trading: bool = False
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    market_source: MarketSourceConfig = Field(default_factory=MarketSourceConfig)
    stocks_interface: StocksInterfaceConfig = Field(
        default_factory=StocksInterfaceConfig
    )
    account_interface: AccountInterfaceConfig = Field(
        default_factory=AccountInterfaceConfig
    )
    strategies: StrategiesConfig = Field(default_factory=StrategiesConfig)
