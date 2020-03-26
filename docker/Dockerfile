FROM python:3.7-slim-buster

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip setuptools \
    && git clone https://github.com/ilcardella/TradingBot /workspace \
    && cd /workspace && python setup.py install \
    && rm -rf /workspace

CMD ["trading_bot"]
