#! /bin/bash
INSTALL_DIR=/opt/TradingBot

echo Installing TradingBot in $INSTALL_DIR...

# Create installation folder
mkdir -p $INSTALL_DIR
mkdir -p $INSTALL_DIR/data
# Copy config files
cp -ar config/ $INSTALL_DIR/config
cp -ar cron/ $INSTALL_DIR/cron
cp -ar scripts $INSTALL_DIR/scripts/
# Make the main script executable
chmod 755 $INSTALL_DIR/scripts/trading_bot.py

echo TradingBot installed.
