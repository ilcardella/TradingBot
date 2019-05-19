ARG BASELINE
FROM ${BASELINE}

# Copy workspace
COPY . /workspace
WORKDIR /workspace

# Install TradingBot with all the dependencies
RUN ./trading_bot.py --install

CMD ["/bin/bash"]
