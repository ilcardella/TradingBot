FROM python:3.8-slim-buster

ARG POETRY_VERSION=1.0.10
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends make \
    && rm -rf /var/lib/apt/lists/* \
    && pip install "poetry==$POETRY_VERSION"

WORKDIR /workspace

COPY ./ /workspace

RUN make install-system \
    && rm -rf /workspace

WORKDIR /

CMD ["trading_bot"]
