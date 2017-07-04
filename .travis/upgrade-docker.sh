#!/usr/bin/env bash

# Upgrade to the latest version of Docker.
sudo apt-get update
sudo apt-get -y -o Dpkg::Options::="--force-confnew" install docker-ce

docker version
