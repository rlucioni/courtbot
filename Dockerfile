FROM python:3.6

ENV TZ /usr/share/zoneinfo/US/Eastern

# See https://docs.docker.com/engine/userguide/eng-image/dockerfile_best-practices/#apt-get
RUN apt-get update && apt-get install -y \
    libqt5webkit5-dev \
    python-lxml \
    qt5-default \
    xvfb

COPY . /src
WORKDIR /src

# TODO: Find out if pip installs can be cached to speed up image build.
RUN make requirements

CMD ["./run.py"]
