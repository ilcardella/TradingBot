FROM python:3.9-slim-buster

ARG POETRY_VERSION
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends make \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --upgrade pip \
    && python -m pip install "poetry==$POETRY_VERSION"

ENV PATH /root/.local/bin:$PATH

WORKDIR /workspace

COPY ./ /workspace

RUN make install-system \
    && rm -rf /workspace

WORKDIR /

CMD ["trading_bot"]
