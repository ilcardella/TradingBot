# Backtesting Guide

The TradingBot now includes powerful backtesting capabilities using the `backtesting.py` library.

## Overview

The backtester allows you to test your trading strategies on historical data to evaluate their performance before risking real money.

## Features

- **CSV Data Input**: Load historical OHLCV data from CSV files
- **Strategy Integration**: Works with all TradingBot strategies (SimpleMACD, VolumeProfile, etc.)
- **Comprehensive Metrics**: Provides detailed performance statistics including:
  - Return on investment
  - Sharpe ratio, Sortino ratio, Calmar ratio
  - Maximum drawdown
  - Win rate and profit factor
  - Trade statistics
- **Visual Reports**: Generates interactive HTML charts showing equity curve, trades, and indicators
- **Risk Management**: Automatic position sizing based on stop loss levels

## CSV File Format

Your CSV file must contain the following columns:

```
Gmt time,Open,High,Low,Close,Volume
```

Example:
```csv
Gmt time,Open,High,Low,Close,Volume
2024-01-01 00:00:00,100.00,102.50,99.50,101.00,1000000
2024-01-02 00:00:00,101.00,103.00,100.50,102.50,1200000
2024-01-03 00:00:00,102.50,104.00,102.00,103.50,1100000
```

## Usage

### Basic Example

```python
from pathlib import Path
from tradingbot.components import Configuration
from tradingbot.components.backtester import Backtester
from tradingbot.components.broker import Broker, BrokerFactory
from tradingbot.strategies import StrategyFactory

# Load configuration
config = Configuration.from_filepath(Path("config/trading_bot.toml"))

# Create broker and strategy
broker = Broker(BrokerFactory(config))
strategy_factory = StrategyFactory(config, broker)
strategy = strategy_factory.make_from_configuration()

# Create backtester
backtester = Backtester(strategy)

# Run backtest
backtester.start(
    csv_path="path/to/your/data.csv",
    cash=10000,        # Initial capital
    commission=0.002   # 0.2% commission per trade
)

# Print results
backtester.print_results()

# Generate plot
backtester.plot_results(filename="backtest_results.html")
```

### Using the Example Script

A ready-to-use example script is provided:

```bash
# Edit the script to point to your CSV file
python examples/run_backtest.py
```

## Configuration

The backtester uses the strategy configured in your `trading_bot.toml` file. To test different strategies, change the `active` strategy in the configuration:

```toml
[strategies]
active = "simple_macd"  # or "volume_profile", etc.
```

## Parameters

### Backtester.start()

- **csv_path** (str): Path to CSV file with OHLCV data
- **cash** (float, default=10000): Initial capital
- **commission** (float, default=0.002): Commission per trade (0.002 = 0.2%)

## Output Metrics

The backtester provides comprehensive performance metrics:

### Returns
- **Return [%]**: Total return percentage
- **Return (Ann.) [%]**: Annualized return
- **Buy & Hold Return [%]**: Comparison to buy-and-hold strategy

### Risk Metrics
- **Sharpe Ratio**: Risk-adjusted return (higher is better)
- **Sortino Ratio**: Downside risk-adjusted return
- **Calmar Ratio**: Return vs maximum drawdown
- **Max. Drawdown [%]**: Largest peak-to-trough decline
- **Volatility (Ann.) [%]**: Annualized volatility

### Trade Statistics
- **# Trades**: Total number of trades
- **Win Rate [%]**: Percentage of profitable trades
- **Profit Factor**: Gross profit / Gross loss
- **Avg. Trade [%]**: Average return per trade
- **Best/Worst Trade [%]**: Best and worst single trade returns

## Tips for Effective Backtesting

1. **Use Sufficient Data**: Ensure you have enough historical data (at least 200+ bars for strategies using EMA 200)

2. **Realistic Commissions**: Set commission rates that match your broker's fees

3. **Avoid Overfitting**: Don't optimize your strategy parameters based solely on backtest results

4. **Consider Slippage**: Real trading may have slippage not captured in backtests

5. **Test Multiple Periods**: Backtest on different time periods to ensure strategy robustness

6. **Compare to Benchmark**: Always compare your strategy's performance to a simple buy-and-hold approach

## Getting Historical Data

You can download historical data from various sources:

- **Yahoo Finance**: Use `yfinance` library to download data
- **Alpha Vantage**: Free API for historical data
- **Your Broker**: Many brokers provide historical data exports
- **TradingView**: Export charts as CSV

Example using yfinance:

```python
import yfinance as yf

# Download data
ticker = yf.Ticker("AAPL")
df = ticker.history(period="1y", interval="1d")

# Save to CSV in the correct format
df.index.name = "Gmt time"
df.rename(columns={
    "Open": "Open",
    "High": "High",
    "Low": "Low",
    "Close": "Close",
    "Volume": "Volume"
}, inplace=True)
df.to_csv("historical_data.csv")
```

## Troubleshooting

### "Not enough data" warnings
- Ensure your CSV has at least 200+ rows for strategies using EMA 200
- Check that your data is properly formatted

### No trades executed
- Your strategy may not be generating signals on the test data
- Try different data or adjust strategy parameters
- Check logs for strategy warnings

### Import errors
- Make sure backtesting.py is installed: `uv add backtesting`
- Ensure all dependencies are up to date: `uv sync`

## Example Output

```
==============================================================
BACKTEST RESULTS
==============================================================
Start                         : 2024-01-01 00:00:00
End                           : 2024-12-31 00:00:00
Duration                      : 365 days 00:00:00
Exposure Time [%]            : 68.5
Equity Final [$]             : 12450.00
Return [%]                   : 24.5
Sharpe Ratio                 : 1.45
Max. Drawdown [%]            : -8.2
# Trades                     : 45
Win Rate [%]                 : 62.2
Profit Factor                : 1.85
==============================================================
```
