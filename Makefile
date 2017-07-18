.DEFAULT_GOAL := help

# Generates a help message. Borrowed from https://github.com/pydanny/cookiecutter-djangopackage.
help: ## Display this help message
	@echo "Please run \`make <target>\` where <target> is one of"
	@perl -nle'print $& if m{^[\.a-zA-Z_-]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

attach: ## Attach to a running courtbot container for debugging
	docker attach courtbot

build: ## Build service images
	docker-compose build

down: ## Stop services
	docker-compose down

encrypt: ## Encrypt secrets
	# https://docs.travis-ci.com/user/encrypting-files/#Encrypting-multiple-files
	tar cvf secrets.tar .docker/env .travis/deploy_key
	travis encrypt-file secrets.tar

logs: ## Tail service logs
	docker-compose logs -f

prune: ## Remove unused images
	docker image prune -af

pull: ## Pull service images from Docker Hub
	docker-compose pull

push: ## Push the rlucioni/courtbot image to Docker Hub
	docker push rlucioni/courtbot

shell: ## Open a shell on a one-off courtbot container
	docker-compose run --rm courtbot /usr/bin/env bash

test: ## Run tests on a one-off courtbot container
	docker-compose run --rm --no-deps courtbot flake8

up: ## Start services in detached mode
	docker-compose up -d
