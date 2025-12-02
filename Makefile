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
> uv run pytest

docs:
> uv run make -C docs html

install:
> uv sync

update:
> uv lock --upgrade
> uv sync

install-system: clean
> uv build
> python3 -m pip install --user dist/*.whl
> mkdir -p $(CONFIG_DIR)
> mkdir -p $(DATA_DIR)
> mkdir -p $(LOG_DIR)
> cp config/trading_bot.toml $(CONFIG_DIR)

build: clean
> uv build

docker: clean
> docker build -t ilcardella/tradingbot -f Dockerfile .

mypy:
> uv run mypy tradingbot/

lint:
> uv run ruff check tradingbot/ test/

format:
> uv run ruff format tradingbot/ test/

format-check:
> uv run ruff format --check tradingbot/ test/

check: install format-check lint mypy test

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
> find . -name '.ruff_cache' -exec rm -rf  {} +

.PHONY: test lint format format-check install docs build docker install-system ci check mypy update clean
