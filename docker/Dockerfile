FROM python:3.8-slim-buster

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip \
    && git clone https://github.com/ilcardella/TradingBot /workspace \
    && cd /workspace && pip install . \
    && rm -rf /workspace

CMD ["trading_bot"]
