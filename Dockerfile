FROM python:3.6

ENV TZ /usr/share/zoneinfo/US/Eastern

# Add Chrome PPA: https://www.ubuntuupdates.org/ppa/google_chrome
# https://docs.docker.com/engine/userguide/eng-image/dockerfile_best-practices/#using-pipes
RUN ["/bin/bash", "-c", "set -o pipefail && curl https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -"]
RUN echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list

# https://docs.docker.com/engine/userguide/eng-image/dockerfile_best-practices/#apt-get
RUN apt-get update && apt-get install -y \
    google-chrome-stable \
    unzip

# Install ChromeDriver.
RUN curl -O https://chromedriver.storage.googleapis.com/2.30/chromedriver_linux64.zip && \
    # unzip does not support reading archives from standard input: https://unix.stackexchange.com/a/2691
    unzip chromedriver_linux64.zip -d /usr/local/bin/ && \
    rm chromedriver_linux64.zip

# Add a non-privileged user with which to run Chrome. Borrowed from
# https://hub.docker.com/r/justinribeiro/chrome-headless/~/dockerfile/.
# This is to account for the fact that running Chrome requires a "privileged"
# container. For more on why the --privileged option is necessary, see
# https://github.com/jessfraz/dockerfiles/issues/65#issuecomment-271085821.
# --cap-add SYS_ADMIN can be used as an alternative to --privileged.
RUN groupadd -r chrome && \
    useradd -r -g chrome -G audio,video chrome && \
    # Give the new user a home directory.
    mkdir -p /home/chrome && \
    chown -R chrome:chrome /home/chrome

# Copying the requirements.txt file separately allows caching of packages installed via pip.
COPY requirements.txt /src/
WORKDIR /src

RUN pip install -r requirements.txt

COPY . /src

# Run Chrome non-privileged.
USER chrome

CMD ["./run.py"]
