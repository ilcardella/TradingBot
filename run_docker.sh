#!/bin/bash

cd app
pip install -r requirements.txt
cd scripts
python trading_bot.py
