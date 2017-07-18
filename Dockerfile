FROM python:3.6

ENV TZ /usr/share/zoneinfo/US/Eastern

# Copying the requirements.txt file separately allows caching of packages installed via pip.
COPY requirements.txt /src/
WORKDIR /src

RUN pip install -r requirements.txt

COPY . /src

CMD ["./run.py"]
