ifeq ($(origin .RECIPEPREFIX), undefined)
  $(error This Make does not support .RECIPEPREFIX. Please use GNU Make 4.0 or later)
endif
.RECIPEPREFIX = >

format:
> poetry run isort tradingbot test
> poetry run black tradingbot test

lint:
> poetry run flake8 tradingbot test

test:
> poetry run pytest

docs:
> poetry run make -C docs html

install:
> poetry install -v

install-system:
> python setup.py install

build:
> poetry build

docker:
> docker build -t tradingbot -f docker/Dockerfile .

ci: install lint test docs build install-system

.PHONY: test lint format install docs build docker install-system ci
