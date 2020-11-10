ifeq ($(origin .RECIPEPREFIX), undefined)
  $(error This Make does not support .RECIPEPREFIX. Please use GNU Make 4.0 or later)
endif
.RECIPEPREFIX = >

INSTALL_DIR = ${HOME}/.TradingBot
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

update:
> poetry update

remove-env:
> poetry env remove python3

install-system: clean
> python3 -m pip install --user .
> mkdir -p $(CONFIG_DIR)
> mkdir -p $(DATA_DIR)
> mkdir -p $(LOG_DIR)
> cp config/trading_bot.toml $(CONFIG_DIR)

build: clean
> poetry build

docker: clean
> docker build -t ilcardella/tradingbot -f docker/Dockerfile .

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

check: install format lint test

ci: check docs build

clean:
> rm -rf *egg-info
> rm -rf build/
> rm -rf dist/
> find . -name '*.pyc' -exec rm -f {} +
> find . -name '*.pyo' -exec rm -f {} +
> find . -name '*~' -exec rm -f  {} +
> find . -name '__pycache__' -exec rm -rf  {} +
> find . -name '_build' -exec rm -rf  {} +
> find . -name '.mypy_cache' -exec rm -rf  {} +
> find . -name '.pytest_cache' -exec rm -rf  {} +

.PHONY: test lint format install docs build docker install-system ci check mypy flake isort black remove update
