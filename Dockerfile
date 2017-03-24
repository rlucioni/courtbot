FROM python:3.6

COPY . /src
WORKDIR /src

RUN make requirements

CMD ["./run.py"]
