# TradingBot
[![Build Status](https://travis-ci.com/ilcardella/TradingBot.svg?branch=master)](https://travis-ci.com/ilcardella/TradingBot)  [![Documentation Status](https://readthedocs.org/projects/tradingbot/badge/?version=latest)](https://tradingbot.readthedocs.io/en/latest/?badge=latest) ![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/ilcardella/tradingbot) ![Docker Pulls](https://img.shields.io/docker/pulls/ilcardella/tradingbot)

This is an attempt to create an autonomous market trading script using the IG
REST API and any other available data source for market prices.

TradingBot is meant to be a "forever running" process that keeps
analysing the markets taking actions whether some conditions are met.
It is halfway from an academic project and a real useful piece of
software, I guess I will see how it goes :)

The main goal of this project is to provide the capability to
write a custom trading strategy with the minimum effort.
TradingBot handles all the boring stuff.

All the credits for the `WeightedAvgPeak` strategy goes to GitHub user @tg12.

## Dependencies

- Python 3.6+
- Poetry (only for development)
- Docker (optional)

View file `pyproject.toml` or `setup.py` for the full list of required python packages.

## Install

First if you have not done yet, install python:
```
sudo apt-get update
sudo apt-get install python3
```

Clone this repo in your workspace and install `TradingBot` by running the following
command in the repository root folder
```
sudo python3 setup.py install
```

## Setup

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
- Copy the `.credentials` file into the `/opt/TradingBot/data` folder
- Revoke permissions to read the file
```
cd data
sudo chmod 600 /opt/TradingBot/data/.credentials
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
how TradingBot work. It is important to setup this file appropriately in order to avoid unexpected behaviours.

## Start TradingBot

You can start TradingBot with
```
sudo trading_bot
```

Otherwise you can change ownership of the `/opt/TradingBot` folder:
```
sudo chown -R $USER: /opt/TradingBot
```
and then run `TradingBot` without sudo
```
trading_bot
```

You can start it in detached mode letting it run in the background with
```
nohup trading_bot >/dev/null 2>&1 &
```

### Close all the open positions

```
trading_bot --close-positions [-c]
```

## Stop TradingBot

To stop a TradingBot instance running in the background
```
ps -ef | grep trading_bot | xargs kill -9
```

## Uninstall
You can use `pip` to uninstall `TradingBot`:
```
sudo pip3 uninstall TradingBot
```

## Development

To ease dependency management there is the `pyproject.toml` helps installing the required
python packages in a isolated virtual environment.

Install `pip` and `poetry` and create the virtual environment:
```
cd /path/to/repository
poetry install
```

## Test

You can run the test from the workspace with:
```
poetry run pytest
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
poetry shell
cd docs
make html
```

The generated html files will be in `docs/_build/html`.

## Automate

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

## Docker

You can run TradingBot in a Docker container (https://docs.docker.com/).

The Docker image is configured with a default TradingBot configuration and it
does not have any `.credentials` files.
**You must mount these files when running the Docker container**

### Pull

You can pull the Docker image directly from the Docker Hub.
Latest version:
```
docker pull ilcardella/tradingbot:latest
```
Tagged version:
```
docker pull ilcardella/tradingbot:v1.2.0
```

### Build
You can build the Docker image yourself using the `Dockerfile` in the `docker` folder:
```
cd /path/to/repo
docker build -t tradingbot -f docker/Dockerfile .
```

### Run
As mentioned above, it's important that you configure TradingBot before starting it.
Once the image is available you can run `TradingBot` in a Docker container mounting the configuration files:
```
docker run -d \
    -v /path/to/config.json:/opt/TradingBot/config/config.json \
    -v /path/to/.credentials:/opt/TradingBot/data/.credentials \
    tradingbot:latest
```

You can also mount the log folder to store the logs on the host adding `-v /host/folder:/opt/TradingBot/log`


## Contributing

Any contribution or suggestion is welcome, please follow the suggested workflow.

### Pull Requests

To add a new feature or to resolve a bug, create a feature branch from the
`master` branch.

Commit your changes and if possible add unit/integration test cases.
Eventually push your branch and create a Pull Request against `master`.

If you instead find problems or you have ideas and suggestions for future
improvements, please open an Issue. Thanks for the support!
