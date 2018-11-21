# TradingBot    [![Build Status](https://travis-ci.com/ilcardella/TradingBot.svg?branch=master)](https://travis-ci.com/ilcardella/TradingBot)  [![Documentation Status](https://readthedocs.org/projects/tradingbot/badge/?version=latest)](https://tradingbot.readthedocs.io/en/latest/?badge=latest)

This is an attempt to create an autonomous market trading script using the IG
REST API and any other available data source for market prices.

TradingBot is meant to be a "forever running" process that keeps
analysing the markets and taking actions whether the conditions are met.
It is halfway from an academic project and a real useful piece of
software, I guess I will see how it goes :)

The main goal of this project is to provide the capability to
write a custom trading strategy with the minimum effort.
TradingBot handle all the boring stuff.

All the credits for the FAIG_iqr strategy goes to GitHub user @tg12
who is the creator of the first script version and gave me a good
starting point for this project. Thank you.

# Dependencies
- Python 3

- numpy
- pandas
- scipy
- matplotlib
- pytz
- requests
- govuk_bank_holidays (https://github.com/ministryofjustice/govuk-bank-holidays)

# Install
TODO (Still need to be properly configured)

Run the shell script `install.sh`.
This will install the script in `/usr/local/TradingBot` folder

# Setup
Install dependencies with pip
```
pip install -r requirements.txt
```

Login to your IG Dashboard
- Obtain an API KEY from the settings panel
- If using the demo account, create demo credentials
- Take note of your spread betting account ID (demo or real)
- Visit AlphaVantage website: `https://www.alphavantage.co`
- Request a free api key
- Insert these info in a file called `.credentials`
This must be in json format
```
{
    "username": "username",
    "password": "password",
    "api_key": "apikey",
    "account_id": "accountId",
    "av_api_key": "apiKey"
}
```
- Copy the `.credentials` file in the `data` folder
- Revoke permissions to read the file if you are paranoid
```
cd data
sudo chmod 600 .credentials
```

You need a file `epic_ids.txt` containg IG epics of the companies you want to monitor.
You can copy this file into the `data` folder.

Open the `config.json` file in the `config` folder and set it up
with the preferred options:

TODO (Explain each configuration parameter)

# Run

Open a new terminal and type:
```
./trading_bot_ctl start
```

To stop instead:
```
./trading_bot_ctl stop
```

To close all the currently open positions:
```
./trading_bot_ctl close-positions
```

# Test

The unit test depend on `pytest` package

```
pip3 install pytest
```

To run the test just use the `pytest` command from the project root.

# Create your own strategy

TODO This process needs some improvements

If you want to create a custom trading strategy, you can create a new
file containing a class that extend from `Strategy` in `Strategy.py`.
You need to override a few methods of that class and then add anything
you require.

After that, if you want TradingBot to use your strategy, just edit the
`StockAutoTrader.py` and instantiate your class.

Please if you create new strategies I would be really happy if you
could share it with me creating a pull request.

# Documentation
Read the documentation at:

https://tradingbot.readthedocs.io

To build it locally you need to install `sphinx` on your machine
http://www.sphinx-doc.org/en/master/usage/installation.html
The `requirements.txt` includes `sphinx` already.

After that you can execute these commands from the project root:
```
sphinx-build -b html doc doc/_build/html
```
or

```
cd doc
make html
```

The generated html files will be under `doc/_build/html`.

# Automate
You can set up the crontab job to run and kill TradinBot at specific times.
The only configuration required is to edit the crontab file adding the preferred schedule:
```
crontab -e
```
As an example this will start TradingBot at 8:00 in the morning and will stop it at 16:35 in the afternoon, every week day (Mon to Fri):
```
00 08 * * 1-5 /.../TradingBot/trading_bot_ctl start
35 16 * * 1-5 /.../TradingBot/trading_bot_ctl stop
```
NOTE: Remember to set the correct installation path and to set the correct timezone in your machine!

# Contributing
I am really happy to receive any help so please just open a pull request
with your changes and I will handle it.

If you instead find problems or have ideas for future improvements open an Issue. Thanks
