#!/usr/bin/env python3
"""
Example script demonstrating how to use the backtester with a CSV file
"""
import logging
from pathlib import Path

from tradingbot.components import Configuration
from tradingbot.components.backtester import Backtester
from tradingbot.components.broker import Broker, BrokerFactory
from tradingbot.strategies import StrategyFactory

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def main():
    """Run backtest example"""
    # Load configuration
    config_path = Path("config/trading_bot.toml")
    if not config_path.exists():
        print(f"Configuration file not found: {config_path}")
        return

    config = Configuration.from_filepath(config_path)

    # Create broker (needed for strategy initialization)
    broker = Broker(BrokerFactory(config))

    # Create strategy from configuration
    strategy_factory = StrategyFactory(config, broker)
    strategy = strategy_factory.make_from_configuration()

    print(f"Using strategy: {strategy.__class__.__name__}")

    # Create backtester
    backtester = Backtester(strategy)

    # Path to CSV file with OHLCV data
    # Expected columns: Gmt time, Open, High, Low, Close, Volume
    csv_path = "data/historical_data.csv"

    if not Path(csv_path).exists():
        print(f"\nCSV file not found: {csv_path}")
        print("\nPlease provide a CSV file with the following columns:")
        print("  - Gmt time (datetime)")
        print("  - Open (float)")
        print("  - High (float)")
        print("  - Low (float)")
        print("  - Close (float)")
        print("  - Volume (float)")
        print("\nExample:")
        print("Gmt time,Open,High,Low,Close,Volume")
        print("2024-01-01 00:00:00,100.0,102.0,99.0,101.0,1000000")
        print("2024-01-02 00:00:00,101.0,103.0,100.0,102.0,1200000")
        return

    # Run backtest
    print(f"\nRunning backtest on {csv_path}...")
    backtester.start(
        csv_path=csv_path,
        cash=10000,  # Initial cash
        commission=0.002,  # 0.2% commission per trade
    )

    # Print results
    print("\n")
    backtester.print_results()

    # Optionally save plot
    plot_file = "backtest_results.html"
    print(f"\nGenerating plot: {plot_file}")
    backtester.plot_results(filename=plot_file)
    print(f"Plot saved! Open {plot_file} in your browser to view.")


if __name__ == "__main__":
    main()
