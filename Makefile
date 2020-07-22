ifeq ($(origin .RECIPEPREFIX), undefined)
  $(error This Make does not support .RECIPEPREFIX. Please use GNU Make 4.0 or later)
endif
.RECIPEPREFIX = >

INSTALL_DIR = /opt/TradingBot
DATA_DIR = $(INSTALL_DIR)/data
CONFIG_DIR = $(INSTALL_DIR)/config
LOG_DIR = $(INSTALL_DIR)/log

default: check

test:
> poetry run python -m pytest

docs:
> poetry run make -C docs html

install:
> poetry install -v

install-system:
> pip install .
> mkdir -p $(CONFIG_DIR)
> mkdir -p $(DATA_DIR)
> mkdir -p $(LOG_DIR)
> cp config/config.json $(CONFIG_DIR)

build:
> poetry build

docker:
> docker build -t tradingbot -f docker/Dockerfile .

mypy:
> poetry run mypy tradingbot/

flake:
> poetry run flake8 tradingbot/ test/

isort:
> poetry run isort tradingbot/ test/

black:
> poetry run black tradingbot/ test/

format: isort black

lint: flake mypy

check: format lint test

ci: install check docs build install-system

.PHONY: test lint format install docs build docker install-system ci check mypy flake isort black
