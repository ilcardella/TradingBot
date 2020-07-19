FROM python:3.8-slim-buster

COPY ./ /workspace
WORKDIR /workspace

RUN pip install --upgrade pip \
    && pip install . \
    && rm -rf /workspace

WORKDIR /

CMD ["trading_bot"]
