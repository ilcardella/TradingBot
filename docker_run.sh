#!/bin/bash

DOCKER_IMAGE=trading_bot
DOCKER_CONTAINER=dkr_trading_bot

start()
{
    docker run -d --rm --init \
        -v ${INSTALL_DIR}:${INSTALL_DIR}:ro
        -v ${HOME}/.TradingBot:/root/.TradingBot \
        ${DOCKER_IMAGE} \
        /opt/TradingBot/src/TradingBot.py
}

build()
{
    docker build \
        --rm \
        --no-cache \
        --build-arg BASELINE=python:3 \
        -f /opt/TradingBot/Dockerfile \
        -t ${DOCKER_IMAGE}
}

help()
{
  echo "Try with:"
  echo "  help - Show this help message"
  echo "  start - Start TradingBot in a Docker container"
  echo "  build - Build the Docker image"
}

case $1 in
  start) start;;
  build) build;;
  *) help;;
esac