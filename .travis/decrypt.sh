#!/usr/bin/env bash

openssl aes-256-cbc -K $encrypted_c58c5a25ed28_key -iv $encrypted_c58c5a25ed28_iv -in secrets.tar.enc -out secrets.tar -d
tar xvf secrets.tar
chmod 600 .travis/deploy_key
