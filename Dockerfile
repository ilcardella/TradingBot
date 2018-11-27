FROM ubuntu

COPY . /app
WORKDIR /app

RUN apt-get install -y python python-pip
RUN pip install -r requirements.txt

CMD ["pytest"]
