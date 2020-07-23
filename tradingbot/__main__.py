#!/usr/bin/env python3

import argparse
import sys

from tradingbot.Components.TimeProvider import TimeProvider
from tradingbot.TradingBot import TradingBot


def get_menu_parser() -> argparse.Namespace:
    # TODO use pip for version
    VERSION = "1.2.0"
    parser = argparse.ArgumentParser(prog="TradingBot")
    main_group = parser.add_mutually_exclusive_group()
    main_group.add_argument(
        "-v", "--version", action="version", version="%(prog)s {}".format(VERSION)
    )
    main_group.add_argument(
        "-c",
        "--close-positions",
        help="Close all the open positions",
        action="store_true",
    )
    backtest_group = parser.add_argument_group("Backtesting")
    backtest_group.add_argument(
        "--backtest",
        help="Backtest the market related to the specified id",
        nargs=1,
        metavar="MARKET_ID",
    )
    backtest_group.add_argument(
        "--epic",
        help="IG epic of the market to backtest. MARKET_ID will be ignored",
        nargs=1,
        metavar="EPIC_ID",
        default=None,
    )
    backtest_group.add_argument(
        "--start",
        help="Start date for the strategy backtest",
        nargs=1,
        metavar="YYYY-MM-DD",
        required="--backtest" in sys.argv,
    )
    backtest_group.add_argument(
        "--end",
        help="End date for the strategy backtest",
        nargs=1,
        metavar="YYYY-MM-DD",
        required="--backtest" in sys.argv,
    )
    return parser.parse_args()


def main() -> None:
    tp = TimeProvider()
    args = get_menu_parser()
    if args.close_positions:
        TradingBot(tp).close_open_positions()
    elif args.backtest and args.start and args.end:
        epic = args.epic[0] if args.epic else None
        TradingBot(tp).backtest(args.backtest[0], args.start[0], args.end[0], epic)
    else:
        TradingBot(tp).start()


if __name__ == "__main__":
    main()
