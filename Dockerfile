FROM python:3.6-alpine

COPY . /spp
WORKDIR /app

RUN pip install -r requirements.txt

CMD ["pytest"]
