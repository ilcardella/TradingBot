# Use Python 3.12 slim as base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install uv for faster package installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /tmp/build

# Copy project files
COPY README.md pyproject.toml uv.lock ./
COPY tradingbot ./tradingbot
COPY config ./config

# Install the package system-wide using uv
RUN uv pip install --system --no-cache .

# Create non-root user
RUN useradd --create-home --shell /bin/bash tradingbot

# Create application directories with proper permissions
RUN mkdir -p /home/tradingbot/.TradingBot/config \
    && mkdir -p /home/tradingbot/.TradingBot/data \
    && mkdir -p /home/tradingbot/.TradingBot/log \
    && chown -R tradingbot:tradingbot /home/tradingbot/.TradingBot

# Copy default configuration
COPY --chown=tradingbot:tradingbot config/trading_bot.toml /home/tradingbot/.TradingBot/config/

# Clean up build directory
RUN rm -rf /tmp/build

# Switch to non-root user
USER tradingbot
WORKDIR /home/tradingbot

# Set the entrypoint to the trading_bot script
CMD ["trading_bot"]
