# TradingBot
This is an attempt to create an autonomous trading script using the IG REST API
and including different customisable strategies.
All the credits for the FAIG_iqr strategy goes to GitHub user 'tg12'
who is the creator of the first script version and gave me a good starting point for this repo

# Dependencies
- Python 3
- numpy
- pandas
- scipy
- matplotlib
- pytz
- requests
- json
- logging
- others...

# Install
Run the shell script `install.sh`.
This will install the script in `/usr/local/TradingBot` folder

# Setup
Install dependencies with pip
```
sudo apt-get install python3-pip
pip3 install 'package1' 'package2' ...
```

Login to your IG Dashboard
- Obtain an API KEY from the settings panel
- If using the demo account, create demo credentials
- Take note of your spread betting account ID (demo or real)
- Insert these info in a file called `.credentials`
This must be in json format
```
{
    "username": "username",
    "password": "password",
    "api_key": "apikey",
    "account_id": "accountId"
}
```
- Copy the `.credentials` file in `/usr/local/TradingBot/config` folder
- Revoke permissions to read the file
```
cd /usr/local/TradingBot/config
sudo chmod 600 .credentials
```

You need a file `epic_ids.txt` containg IG epic of the company you want to analyse.
You can copy this file into `/usr/local/TradingBot/data`

Add the path `/usr/local/TradingBot` to your env PATH variable

# Run
Open a new terminal and type:
```
trading_bot_ctl start
```

To stop instead:
```
trading_bot_ctl stop
```

# Automate
You can set up the crontab job to run and kill TradinBot at specific times.
The only configuration required is to edit the crontab file adding the preferred schedule:
```
crontab -e
```
As an example this will start TradingBot at 8:00 in the morning and will stop it at 16:35 in the afternoon, every week day (Mon to Fri):
```
00 08 * * 1-5 /usr/local/TradingBot/trading_bot_ctl start
35 16 * * 1-5 /usr/local/TradingBot/trading_bot_ctl stop
```
NOTE: Remember to set the correct installation path and to set the correct timezone in your machine!
