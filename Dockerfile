FROM python:3.7-slim-buster

# Copy workspace
COPY . /workspace
WORKDIR /workspace

# Prepare environment
#RUN pip install pipenv
#    && pipenv lock -r > requirements.txt
#    && pip install -r requirements.txt
#    && rm requirements.txt

# Install TradingBot
RUN python setup.py install

CMD ["trading_bot"]
