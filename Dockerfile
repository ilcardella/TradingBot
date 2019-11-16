FROM python:3.7-slim-buster

# Copy workspace
COPY . /workspace
WORKDIR /workspace

RUN pip install pipenv
# Install TradingBot
RUN python setup.py install

CMD ["trading_bot"]
