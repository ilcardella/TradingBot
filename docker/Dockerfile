FROM python:3.10-slim-buster

ARG POETRY_VERSION
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    libssl-dev \
    libffi-dev \
    python-dev \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --upgrade pip \
    && python -m pip install poetry

ENV PATH=/root/.local/bin:$PATH

WORKDIR /workspace
COPY ./ /workspace

RUN make install-system \
    && rm -rf /workspace

WORKDIR /

CMD ["trading_bot"]
