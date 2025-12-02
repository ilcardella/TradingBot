# Use a multi-stage build to keep the final image small
FROM python:3.12-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files first to leverage cache
COPY README.md pyproject.toml uv.lock ./

# Install dependencies into a virtual environment
# We use --no-dev to exclude development dependencies
# We use --compile-bytecode to speed up startup
RUN uv sync --frozen --no-dev --compile-bytecode

# Copy the rest of the application
COPY . .

# Install the project itself
RUN uv sync --frozen --no-dev --compile-bytecode

# Runtime stage
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# Create a non-root user for security
RUN useradd --create-home appuser
WORKDIR /home/appuser
USER appuser

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy configuration and data directories if needed
# Assuming the app expects config in specific locations, we might need to adjust
# For now, we'll just ensure the user has a place to put data
RUN mkdir -p /home/appuser/.TradingBot/config \
    && mkdir -p /home/appuser/.TradingBot/data \
    && mkdir -p /home/appuser/.TradingBot/log

# Copy default config if it exists in the repo
COPY --chown=appuser:appuser config/trading_bot.toml /home/appuser/.TradingBot/config/trading_bot.toml

# Set the entrypoint
CMD ["trading_bot"]
