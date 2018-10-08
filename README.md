# TradingBot
This is an attempt to create an autonomous trading script using the IG REST API
and including different customisable strategies.
All the credits for the FAIG_iqr strategy goes to GitHub user 'tg12'
who is the creator of the first script version and gave me a good starting point for this repo

# Dependencies
Python 3
numpy
pandas
scipy
matplotlib

# Setup
Install dependency with pip3
- sudo apt-get install python3-pip
- pip3 install package

Login to your IG Dashboard
- Obtain an API KEY from the settings
- Take note of your spread betting account ID (demo or real)
- Insert these info in the config.json file (double check the other info as well)

# Run
From the project root folder:
- cd scripts
- python3 main.py username password
