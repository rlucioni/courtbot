#!/usr/bin/env bash

# We only want to push to Docker Hub on pushes to master (e.g., after merging
# a pull request). See https://github.com/travis-ci/travis-ci/issues/6652#issuecomment-255597049.
if [ ${TRAVIS_PULL_REQUEST_BRANCH:-$TRAVIS_BRANCH} == "master" ]; then
    docker login -u="$DOCKER_USERNAME" -p="$DOCKER_PASSWORD"
    make push
    echo Pushed a new rlucioni/courtbot image to Docker Hub.
else
    echo Skipping push to Docker Hub.
fi
