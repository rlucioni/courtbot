#!/usr/bin/env bash

# Upgrade to Docker Compose 1.14.0
sudo rm /usr/local/bin/docker-compose
curl -L https://github.com/docker/compose/releases/download/1.14.0/docker-compose-`uname -s`-`uname -m` > docker-compose
chmod +x docker-compose
sudo mv docker-compose /usr/local/bin

docker-compose --version
