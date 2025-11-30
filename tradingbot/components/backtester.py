import logging
from typing import Optional

import pandas as pd
from backtesting import Backtest
from backtesting import Strategy as BacktestStrategy

from ..components import TradeDirection
from ..strategies import StrategyImpl


class TradingBotStrategy(BacktestStrategy):
    """
    Adapter class that wraps our TradingBot strategies to work with backtesting.py
    """

    def init(self):
        """Initialize the strategy with the wrapped TradingBot strategy"""
        # The wrapped strategy will be set externally
        self.wrapped_strategy = None
        self.signals = []

    def next(self):
        """Called on each bar to generate trading signals"""
        if self.wrapped_strategy is None:
            return

        # Create a mock market object with current price data
        class MockMarket:
            def __init__(self, data):
                self.bid = float(data.Close[-1])
                self.offer = float(data.Close[-1])
                self.epic = "BACKTEST"
                self.id = "BACKTEST"

        # Create a mock datapoints object with historical data
        class MockDatapoints:
            def __init__(self, df):
                self.dataframe = df

        # Get all historical data up to current point
        historical_data = pd.DataFrame(
            {
                "close": self.data.Close[:],
                "high": self.data.High[:],
                "low": self.data.Low[:],
                "volume": self.data.Volume[:],
            }
        )

        mock_market = MockMarket(self.data)
        mock_datapoints = MockDatapoints(historical_data)

        # Get signal from wrapped strategy
        try:
            trade_direction, limit, stop = self.wrapped_strategy.find_trade_signal(
                mock_market, mock_datapoints
            )

            # Execute trades based on signal
            if trade_direction == TradeDirection.BUY:
                if not self.position:
                    # Calculate position size based on stop loss if available
                    if stop and stop > 0:
                        risk_per_trade = self.equity * 0.02  # Risk 2% per trade
                        stop_distance = abs(self.data.Close[-1] - stop)
                        if stop_distance > 0:
                            size = risk_per_trade / stop_distance
                            self.buy(size=min(size, 1.0), sl=stop, tp=limit)
                        else:
                            self.buy()
                    else:
                        self.buy()

            elif trade_direction == TradeDirection.SELL:
                if not self.position:
                    # Calculate position size based on stop loss if available
                    if stop and stop > 0:
                        risk_per_trade = self.equity * 0.02  # Risk 2% per trade
                        stop_distance = abs(stop - self.data.Close[-1])
                        if stop_distance > 0:
                            size = risk_per_trade / stop_distance
                            self.sell(size=min(size, 1.0), sl=stop, tp=limit)
                        else:
                            self.sell()
                    else:
                        self.sell()

            # Close position if we get opposite signal
            elif self.position:
                self.position.close()

        except Exception as e:
            logging.debug(f"Error in strategy execution: {e}")


class Backtester:
    """
    Provides capability to backtest strategies using backtesting.py library
    """

    strategy: StrategyImpl
    result: Optional[pd.Series]
    backtest: Optional[Backtest]

    def __init__(self, strategy: StrategyImpl) -> None:
        logging.info("Backtester created")
        self.strategy = strategy
        self.result = None
        self.backtest = None

    def load_data_from_csv(self, csv_path: str) -> pd.DataFrame:
        """
        Load OHLCV data from CSV file.
        Expected columns: Gmt time, Open, High, Low, Close, Volume
        """
        logging.info(f"Loading data from {csv_path}")

        # Read CSV
        df = pd.read_csv(csv_path)

        # Rename columns to match backtesting.py requirements
        column_mapping = {
            "Gmt time": "Date",
            "Open": "Open",
            "High": "High",
            "Low": "Low",
            "Close": "Close",
            "Volume": "Volume",
        }

        # Check if columns exist (case-insensitive)
        df.columns = df.columns.str.strip()
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df.rename(columns={old_col: new_col}, inplace=True)

        # Parse date and set as index
        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)

        # Ensure numeric types
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Drop any rows with NaN values
        df.dropna(inplace=True)

        # Sort by date
        df.sort_index(inplace=True)

        logging.info(
            f"Loaded {len(df)} rows of data from {df.index[0]} to {df.index[-1]}"
        )

        return df

    def start(
        self, csv_path: str, cash: float = 10000, commission: float = 0.002
    ) -> None:
        """
        Run backtest on data from CSV file

        Args:
            csv_path: Path to CSV file with OHLCV data
            cash: Initial cash amount (default: 10000)
            commission: Commission percentage per trade (default: 0.002 = 0.2%)
        """
        logging.info(
            f"Starting backtest with {cash} initial cash and {commission * 100}% commission"
        )

        # Load data
        data = self.load_data_from_csv(csv_path)

        # Create backtesting.py Backtest instance
        self.backtest = Backtest(
            data,
            TradingBotStrategy,
            cash=cash,
            commission=commission,
            exclusive_orders=True,
        )

        # Inject our strategy into the backtesting strategy
        # We need to do this via a custom init
        original_init = TradingBotStrategy.init

        def custom_init(bt_strategy):
            original_init(bt_strategy)
            bt_strategy.wrapped_strategy = self.strategy

        TradingBotStrategy.init = custom_init  # type: ignore

        # Run backtest
        logging.info("Running backtest...")
        self.result = self.backtest.run()

        # Restore original init
        TradingBotStrategy.init = original_init  # type: ignore

        logging.info("Backtest completed")

    def print_results(self) -> None:
        """Print backtest results"""
        if self.result is None:
            logging.warning("No backtest results available. Run start() first.")
            return

        logging.info("=" * 60)
        logging.info("BACKTEST RESULTS")
        logging.info("=" * 60)

        # Print key metrics
        metrics = {
            "Start": self.result.get("Start"),
            "End": self.result.get("End"),
            "Duration": self.result.get("Duration"),
            "Exposure Time [%]": self.result.get("Exposure Time [%]"),
            "Equity Final [$]": self.result.get("Equity Final [$]"),
            "Equity Peak [$]": self.result.get("Equity Peak [$]"),
            "Return [%]": self.result.get("Return [%]"),
            "Buy & Hold Return [%]": self.result.get("Buy & Hold Return [%]"),
            "Return (Ann.) [%]": self.result.get("Return (Ann.) [%]"),
            "Volatility (Ann.) [%]": self.result.get("Volatility (Ann.) [%]"),
            "Sharpe Ratio": self.result.get("Sharpe Ratio"),
            "Sortino Ratio": self.result.get("Sortino Ratio"),
            "Calmar Ratio": self.result.get("Calmar Ratio"),
            "Max. Drawdown [%]": self.result.get("Max. Drawdown [%]"),
            "Avg. Drawdown [%]": self.result.get("Avg. Drawdown [%]"),
            "Max. Drawdown Duration": self.result.get("Max. Drawdown Duration"),
            "Avg. Drawdown Duration": self.result.get("Avg. Drawdown Duration"),
            "# Trades": self.result.get("# Trades"),
            "Win Rate [%]": self.result.get("Win Rate [%]"),
            "Best Trade [%]": self.result.get("Best Trade [%]"),
            "Worst Trade [%]": self.result.get("Worst Trade [%]"),
            "Avg. Trade [%]": self.result.get("Avg. Trade [%]"),
            "Max. Trade Duration": self.result.get("Max. Trade Duration"),
            "Avg. Trade Duration": self.result.get("Avg. Trade Duration"),
            "Profit Factor": self.result.get("Profit Factor"),
            "Expectancy [%]": self.result.get("Expectancy [%]"),
            "SQN": self.result.get("SQN"),
        }

        for key, value in metrics.items():
            if value is not None:
                logging.info(f"{key:30s}: {value}")

        logging.info("=" * 60)

    def plot_results(self, filename: Optional[str] = None) -> None:
        """
        Plot backtest results

        Args:
            filename: Optional filename to save the plot (e.g., 'backtest_results.html')
        """
        if self.backtest is None:
            logging.warning("No backtest available. Run start() first.")
            return

        logging.info("Generating backtest plot...")
        self.backtest.plot(filename=filename, open_browser=False)
        if filename:
            logging.info(f"Plot saved to {filename}")
