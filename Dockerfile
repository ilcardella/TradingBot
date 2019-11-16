FROM python:3.7-slim-buster

RUN pip install pipenv

# Copy workspace
COPY . /workspace
WORKDIR /workspace

# Install TradingBot
RUN python setup.py install

# Default command
CMD ["trading_bot"]
