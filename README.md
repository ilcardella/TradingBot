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
- Insert these info in a file called `.credentials` inside the `config` folder
This must be in json format
```
{
    "username": "username",
    "password": "password",
    "api_key": "apikey",
    "account_id": "accountId"
}
```
- Revoke permissions to read the file
```
cd config
sudo chmod 600 .credentials
```

# Run
From the project root folder:
```
cd scripts
python3 main.py
```
