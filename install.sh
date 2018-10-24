#!/bin/bash
INSTALL_DIR=/usr/local/TradingBot

echo Installing TradingBot in $INSTALL_DIR...

# Create installation folder
mkdir -p $INSTALL_DIR
mkdir -p $INSTALL_DIR/data
# Copy files
cp -ar config/ $INSTALL_DIR/config
cp -ar cron/trading_bot_ctl $INSTALL_DIR
cp -ar scripts/ $INSTALL_DIR/scripts
# Make the main script executable
chmod 755 $INSTALL_DIR/trading_bot_ctl

echo TradingBot installed.
echo Follow setup instructions at: https://github.com/ilcardella/TradingBot
echo Remember to configure TradingBot editing the config.json file too!
