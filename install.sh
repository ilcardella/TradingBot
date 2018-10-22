#! /bin/bash

INSTALL_DIR=/opt/TradingBot

echo Installing TradingBot in $INSTALL_DIR...

cp scripts/ $INSTALL_DIR/scripts
cp config/ $INSTALL_DIR/config
cp cron/ $INSTALL_DIR/cron
mkdir $INSTALL_DIR/data


echo TradingBot installed.
