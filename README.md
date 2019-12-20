# TradingBot
[![Build Status](https://travis-ci.com/ilcardella/TradingBot.svg?branch=master)](https://travis-ci.com/ilcardella/TradingBot)  [![Documentation Status](https://readthedocs.org/projects/tradingbot/badge/?version=latest)](https://tradingbot.readthedocs.io/en/latest/?badge=latest)

This is an attempt to create an autonomous market trading script using the IG
REST API and any other available data source for market prices.

TradingBot is meant to be a "forever running" process that keeps
analysing the markets and taking actions whether the conditions are met.
It is halfway from an academic project and a real useful piece of
software, I guess I will see how it goes :)

The main goal of this project is to provide the capability to
write a custom trading strategy with the minimum effort.
TradingBot handle all the boring stuff.

All the credits for the `WeightedAvgPeak` strategy goes to GitHub user @tg12
who is the creator of the first script version and gave me a good
starting point for this project. Thank you.

# Dependencies

- Python 3.5+
- Pipenv (optional)
- Docker (optional)

View file `Pipfile` or `setup.py` for the full list of required python packages.

# Install

First if you have not yet done so, install python 3.5+ and pipenv
```
sudo apt-get update
sudo apt-get install python3 python3-pip
```

Clone this repo in your workspace and install `TradingBot` by running the following
command in the repository root folder
```
python setup.py install
```

# Setup

Login to your IG Dashboard

- Obtain an API KEY from the settings panel
- If using the demo account, create demo credentials
- Take note of your spread betting account ID (demo or real)
- Visit AlphaVantage website: `https://www.alphavantage.co`
- Request a free api key
- Insert these info in a file called `.credentials`

This must be in json format
```json
{
    "username": "username",
    "password": "password",
    "api_key": "apikey",
    "account_id": "accountId",
    "av_api_key": "apiKey"
}
```
- Copy the `.credentials` file into the `$HOME/.TradingBot/data` folder
- Revoke permissions to read the file
```
cd data
sudo chmod 600 $HOME/.TradingBot/data/.credentials
```

### Market source

There are different ways to define which markets to analyse with TradinbgBot. You can select your preferred option in the `config.json` file with the `market_source` parameter:

- **Local file**

You can create a file `epic_ids.txt` containg IG epics of the companies you want to monitor.
You need to copy this file into the `data` folder.

- **Watchlist**

You can use an IG watchlist, TradingBot will analyse every market added to the selected watchlist

- **API**

TradingBot navigates the IG markets dynamically using the available API call to fetch epic ids.

### Configuration file

The `config.json` file is in the `config` folder and it contains several configurable parameter to personalise
how TradingBot work. These are the description of each parameter:

#### General

- **max_account_usable**: The maximum percentage of account funds to use (A safe value is around 50%)
- **time_zone**: The timezone to use (i.e. 'Europe/London)
- **enable_log**: Enable the log in a file rather than on stdout
- **log_file**: Define the full file path for the log file to use, if enabled. {home} and {timestamp} placeholders are replaced with the user home directory and the timestamp when TradingBot started
- **debug_log**: Enable the debug level in the logging
- **credentials_filepath**: Filepath for the `.credentials` file
- **market_source**: The source to use to fetch the market ids. Available values as explained above are: [`list`, `watchlist`, `api`]
- **epic_ids_filepath**:  The full file path for the local file containing the list of epic ids
- **watchlist_name**: The watchlist name to use as market source, if selected
- **active_strategy**: The strategy name to use. Must match one of the names in the `Strategies` section below
- **spin_interval**: The amount of seconds that TradinBot waits for after it ends processing the markets, before starting over.

#### IG Interface

- **order_type**: The IG order type (MARKET, LIMIT, etc.). Do NOT change it
- **order_size**: The size of the spread bets
- **order_expiry**: The order expiry (DFB). Do NOT change it
- **order_currency**: The currency of the order (For UK shares leave it as GBP)
- **order_force_open**: Force to open the orders
- **use_g_stop**: Use guaranteed stops. Read IG terms for more info about them.
- **use_demo_account**: Trade on the DEMO IG account. If enabled remember to setup the demo account credentials too
- **controlled_risk**: Enable the controlled risk stop loss calculation. Enable only if you have a controlled risk account.
- **paper_trading**: Enable the `paper trading`. No real trades will be done on the IG account.

#### Alpha Vantage

- **enable**: Enable the use of AlphaVantage API
- **api_timeout**: Timeout in seconds between each API call

#### Strategies

Settings specific for each strategy

#### SimpleMACD

- **max_spread_perc**: Spread percentage to filter markets with high spread
- **limit_perc**: Limit percentage to take profit for each trade
- **stop_perc**: Stop percentage to stop any loss


# Start TradingBot

You can start TradingBot in your current terminal
```
trading_bot
```
or you can start it in detached mode, letting it run in the background
```
nohup trading_bot >/dev/null 2>&1 &
```

### Close all the open positions

```
trading_bot -c
```

# Stop TradingBot

To stop a TradingBot instance running in the background
```
ps -ef | grep trading_bot | xargs kill -9
```

# Development

To ease dependency management there is `Pipfile` which helps installing the required
python packages in a isolated virtual environment.

Install `pipenv`:
```
sudo -H pip3 install -U pipenv
```

Create the virtual environment:
```
pipenv install --dev
```

## Test

You can run the test from the workspace with:
```
pipenv run pytest
```

## Documentation

The Sphinx documentation contains further details about each TradingBot module
with source code documentation of each class member.
Explanation is provided regarding how to create your own Strategy and how to integrate
it with the system.

Read the documentation at:

https://tradingbot.readthedocs.io

You can build it locally with:
```
pipenv run sphinx-build -nWT -b html doc doc/_build/html
```

The generated html files will be in `doc/_build/html`.

# Automate

**NOTE**: TradingBot monitors the market opening hours and suspend the trading when the market is closed. Generally you should NOT need a cron job!

You can set up the crontab job to run and kill TradinBot at specific times.
The only configuration required is to edit the crontab file adding the preferred schedule:
```
crontab -e
```
As an example this will start TradingBot at 8:00 in the morning and will stop it at 16:35 in the afternoon, every week day (Mon to Fri):
```shell
00 08 * * 1-5 trading_bot
35 16 * * 1-5 kill -9 $(ps | grep trading_bot | grep -v grep | awk '{ print $1 }')
```
NOTE: Remember to set the correct timezone in your machine!

# Docker

You can run TradingBot in a Docker container (https://docs.docker.com/).

First you need to install `TradingBot` as explained above.

Then you can build the Docker image used by `TradingBot`:
```
./docker_ctl build
```

Once the image is built you can run `TradingBot` in a Docker container:
```
./docker_ctl start
```

The container will be called `trading_bot` and the logs will still be stored in the configured folder in the host machine. By default `$HOME/.TradingBot/log`.

Check the `Dockerfile` and the  `docker_ctl` script for more details

To stop the TradingBot container:
```
docker kill trading_bot
```

If you need to start a bash shell into a running container
```
docker exec -it trading_bot bash
```

# Contributing

Any contribution or suggestion is welcome, please follow the suggested workflow.

### Pull Requests

To add a new feature or to resolve a bug, create a feature branch from the
`master` branch.

Commit your changes and if possible add unit/integration test cases.
Eventually push your branch and create a Pull Request against `master`.

If you instead find problems or you have ideas and suggestions for future
improvements, please open an Issue. Thanks for the support!
