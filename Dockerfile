FROM python:3.6

RUN apt-get update

COPY . /src
WORKDIR /src

RUN make requirements

CMD ["./run.py"]
