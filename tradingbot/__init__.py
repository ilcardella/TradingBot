import argparse
import sys
from pathlib import Path

from .components import TimeProvider
from .trading_bot import TradingBot


def get_menu_parser() -> argparse.Namespace:
    VERSION = "2.0.0"
    parser = argparse.ArgumentParser(prog="TradingBot")
    parser.add_argument(
        "-f",
        "--config",
        help="Configuration file path",
        metavar="FILEPATH",
        type=Path,
    )
    main_group = parser.add_mutually_exclusive_group()
    main_group.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {VERSION}"
    )
    main_group.add_argument(
        "-c",
        "--close-positions",
        help="Close all the open positions",
        action="store_true",
    )
    main_group.add_argument(
        "-b",
        "--backtest",
        help="Run backtest using CSV file with OHLCV data (columns: Gmt time, Open, High, Low, Close, Volume)",
        nargs=1,
        metavar="CSV_FILE",
    )
    main_group.add_argument(
        "-s",
        "--single-pass",
        help="Run a single iteration on the market source",
        action="store_true",
    )
    backtest_group = parser.add_argument_group("Backtesting")
    backtest_group.add_argument(
        "--cash",
        help="Initial cash for backtesting (default: 10000)",
        type=float,
        default=10000,
        metavar="AMOUNT",
    )
    backtest_group.add_argument(
        "--commission",
        help="Commission per trade as percentage (default: 0.2)",
        type=float,
        default=0.2,
        metavar="PERCENT",
    )
    backtest_group.add_argument(
        "--plot",
        help="Save backtest plot to specified HTML file",
        nargs=1,
        metavar="FILENAME",
        default=None,
    )
    return parser.parse_args()


def main() -> None:
    args = get_menu_parser()

    # For backtesting, we don't need full TradingBot initialization (no broker/auth required)
    if args.backtest:
        from .components import Configuration
        from .strategies import StrategyFactory
        from .components import Backtester

        # Load configuration
        config = Configuration.from_filepath(args.config)

        # Create a minimal broker-like object for strategy initialization
        # The strategy won't actually use broker methods during backtesting
        class MockBroker:
            pass

        mock_broker = MockBroker()

        # Create strategy
        strategy = StrategyFactory(config, mock_broker).make_from_configuration()

        # Create backtester
        backtester = Backtester(strategy)

        # Convert commission from percentage to decimal
        commission = args.commission / 100.0
        plot_file = args.plot[0] if args.plot else None

        # Run backtest
        backtester.start(
            csv_path=args.backtest[0],
            cash=args.cash,
            commission=commission,
        )

        # Print results
        backtester.print_results()

        # Generate plot if requested
        if plot_file:
            backtester.plot_results(filename=plot_file)
    else:
        # For normal trading operations, initialize full TradingBot
        bot = TradingBot(time_provider=TimeProvider(), config_filepath=args.config)
        if args.close_positions:
            bot.close_open_positions()
        else:
            bot.start(single_pass=args.single_pass)
