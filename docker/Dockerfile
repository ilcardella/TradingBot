FROM python:3.8-slim-buster

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends make \
    && rm -rf /var/lib/apt/lists/* \
    && pip install 'poetry==1.0.5'

WORKDIR /workspace

COPY ./ /workspace

RUN make install-system \
    && rm -rf /workspace

WORKDIR /

CMD ["trading_bot"]
