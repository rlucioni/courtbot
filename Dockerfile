FROM python:3.6

ENV TZ /usr/share/zoneinfo/US/Eastern

# See https://docs.docker.com/engine/userguide/eng-image/dockerfile_best-practices/#apt-get
RUN apt-get update && apt-get install -y \
    libqt5webkit5-dev \
    python-lxml \
    qt5-default \
    xvfb

# Copying the requirements.txt file separately allows caching of packages installed via pip.
COPY requirements.txt /src/
WORKDIR /src

RUN pip install -r requirements.txt

COPY . /src

CMD ["./run.py"]
