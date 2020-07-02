ifeq ($(origin .RECIPEPREFIX), undefined)
  $(error This Make does not support .RECIPEPREFIX. Please use GNU Make 4.0 or later)
endif
.RECIPEPREFIX = >

format:
> poetry run black .

lint:
> poetry run flake8

test:
> poetry run pytest

docs:
> poetry run make -C docs html

install:
> poetry install -v

install-setup:
> python setup.py install

build:
> poetry build

docker:
> docker build -t tradingbot -f docker/Dockerfile .

ci: install format lint test docs build install-setup docker

.PHONY: test lint format install docs build docker install-setup ci
