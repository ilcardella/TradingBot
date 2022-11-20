# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## []
### Added
- Input CLI parameter `--config` to specify a configuration file
- Added `simple_boll_bands` strategy
- Added `--single-pass` optional argument to perform a single iteration of the strategy
- Support for Python 3.9
- IGInterface `api_timeout` configuration parameter to pace http requests

### Changed
- Moved `paper_trading` configuration outside of the single broker interface
- Converted configuration file from `json` to `toml` format
- YFinance interface fetch only necessary data for specified data range
- When using a watchlist as market source, markets are only fetched once

### Fixed
- Bug preventing to process trade when account does not hold any position yet
- Fixed arm64 docker image build adding missing build dependencies
- Issue 372 - Fixed security warning in ig_interface.py logging
- Issue 358 - Removed default value for `--config` optional argument

### Removed
- Support for Python 3.6 and 3.7

## [2.0.0] - 2020-07-29
### Changed
- Improved and expanded configuration file format
- TradingBot is installed in the user space and support files in the user home folder
- Moved main function in `tradingbot` init module
- Replaced dependency manager with Dependabot

### Fixed
- Broker package missing __init__.py
- Module imports to absolute from installed main package

### Removed
- Support of Python 3.5
- Setup.py configuration

### Added
- Common interfaces to unify stocks and account interfaces
- Support for Yahoo Finance
- Formatting and linting support with black and flake8
- Static types checking with mypy
- Make `install-system` target to install TradingBot
- Support Docker image on aarch64 architecture

## [1.2.0] - 2019-11-16
### Added
- Added backtesting feature
- Created Components module
- Added TimeProvider module
- Added setup.py to handle installation

### Changed
- Updated CI configuration to test the Docker image
- Updated the Docker image with TradingBot already installed

## [1.1.0] - 2019-09-01
### Changed
- Replaced bash script with python
- Moved sources in `src` installation folder
- Corrected IGInterface numpy dependency
- Added Pipenv integration
- Exported logic from Custom Strategy to simplify workflow
- Added dev-requirements.txt for retro compatibility
- Updated Sphinx documentation

## [1.0.1] - 2019-05-09
### Changed
- Updated renovate configuration

## [1.0.0] - 2019-04-21
### Added
- Initial release
