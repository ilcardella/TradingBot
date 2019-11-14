ARG BASELINE
FROM ${BASELINE}

# Copy workspace
COPY . /workspace
WORKDIR /workspace

# Prepare environment
RUN pip install pipenv
RUN pipenv install

# Install TradingBot
RUN ./install.py

CMD ["/bin/bash"]
