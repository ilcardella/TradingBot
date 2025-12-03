# TradingBot
![Build Status](https://github.com/ilcardella/TradingBot/workflows/TradingBot%20CI/badge.svg) ![Documentation Status](https://readthedocs.org/projects/tradingbot/badge/?version=latest) ![Docker Pulls](https://img.shields.io/docker/pulls/ilcardella/tradingbot)

This is an attempt to create an autonomous market trading script using the IG
REST API and any other available data source for market prices.

TradingBot is meant to be a "forever running" process that keeps
analysing the markets taking actions whether some conditions are met.
It is halfway from an academic project and a real useful piece of
software, I guess I will see how it goes :)

The main goal of this project is to provide the capability to
write a custom trading strategy with minimal effort.
TradingBot handles all the boring stuff.

## Dependencies

- Python 3.10+
- UV (only for development)
- Docker (optional)

## Install

Clone this repo and install `TradingBot` by running the following command from
the repository root folder
```bash
make install-system
```

## Setup

Login to your IG Index dashboard

- Obtain an API KEY from the settings panel
- If using the demo account, create demo credentials
- Take note of your spread betting account ID (demo or real)
- (Optional) Visit AlphaVantage website: `https://www.alphavantage.co` and request a free api key
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
- Copy the `.credentials` file into the `${HOME}/.TradingBot/config` folder
- Revoke permissions to read the file from other users
```bash
cd config
sudo chmod 600 ${HOME}/.TradingBot/config/.credentials
```

### Market source

There are different ways to define which markets to analyse with TradinbgBot. You can select your preferred option in the configuration file under the `market_source` section:

- **Local file**

You can create a file `epic_ids.txt` containg IG epics of the companies you want to monitor.
You need to copy this file into the `${HOME}/.TradingBot/data` folder.

- **Watchlist**

You can use an IG watchlist, TradingBot will analyse every market added to the selected watchlist

- **API**

TradingBot navigates the IG markets dynamically using the available API call to fetch epic ids.

### Configuration file

The configuration file is in the `config` folder and it contains several configurable parameter to personalise
how TradingBot work. It is important to setup this file appropriately in order to avoid unexpected behaviours.

## Start TradingBot

You can start TradingBot with
```bash
trading_bot
```

### Close all the open positions

```bash
trading_bot --close-positions [-c]
```


## Uninstall
You can use `pip` to uninstall `TradingBot`:
```bash
sudo pip3 uninstall TradingBot
```

## Development

The `Makefile` is the entrypoint for any development action.
`uv` handles the dependency management and the `pyproject.toml` contains the required
python packages.

Install [uv](https://python-uv.org/docs/) and create the virtual environment:
```bash
cd /path/to/repository
make install
```

## Test

You can run the test from the workspace with:
```
make test
```

## Documentation

The Sphinx documentation contains further details about each TradingBot module
with source code documentation of each class member.
Explanation is provided regarding how to create your own Strategy and how to integrate
it with the system.

Read the documentation at:

https://tradingbot.readthedocs.io

You can build it locally with:
```bash
make docs
```

The generated html files will be in `docs/_build/html`.

## Docker

You can run TradingBot in a [Docker](https://docs.docker.com/) container.

The Docker images are configured with a default TradingBot configuration and it
does not have any `.credentials` files.
**You must mount these files when running the Docker container**

### Pull

The Docker images are available in the official [Docker Hub](https://hub.docker.com/r/ilcardella/tradingbot).
Currently `TradingBot` supports both `amd64` and `arm64` architectures.
You can pull the Docker image directly from the Docker Hub.
Latest version:
```bash
docker pull ilcardella/tradingbot:latest
```

### Build
You can build the Docker image yourself using the `Dockerfile` in the `docker` folder:
```bash
cd /path/to/repo
make docker
```

### Run
As mentioned above, it's important that you configure TradingBot before starting it.
Once the image is available you can run `TradingBot` in a Docker container mounting the configuration files:
```bash
docker run -d \
    -v /path/to/trading_bot.toml:/.TradingBot/config/trading_bot.toml \
    -v /path/to/.credentials:/.TradingBot/config/.credentials \
    tradingbot:latest
```

You can also mount the log folder to store the logs on the host adding `-v /host/folder:/.TradingBot/log`
