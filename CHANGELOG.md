# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## []
### Changed
- Improved and expanded configuration file format
- TradingBot is installed in the user space and support files in the user home folder

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
