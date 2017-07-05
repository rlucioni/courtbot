#!/usr/bin/env bash

docker login -u="$DOCKER_USERNAME" -p="$DOCKER_PASSWORD"
make push
echo "Pushed a new rlucioni/courtbot image to Docker Hub."

mkdir artifact
cp -R .docker artifact/.docker
cp docker-compose.yml artifact/docker-compose.yml
cp Makefile artifact/Makefile
cp .travis/update.sh artifact/update.sh

# The syntax of the arguments provided here is important! We want to copy the
# contents of the artifact directory over the contents of the courtbot directory,
# creating it if it doesn't exist.
scp -o StrictHostKeyChecking=no -i .travis/deploy_key -r artifact/. travis@${DROPLET_IP}:courtbot/
echo "Copied build artifact to production host."

ssh -o StrictHostKeyChecking=no -i .travis/deploy_key travis@${DROPLET_IP} "cd courtbot && ./update.sh"
echo "Deployment complete."
