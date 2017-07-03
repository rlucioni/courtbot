.DEFAULT_GOAL := run

# Generates a help message. Borrowed from https://github.com/pydanny/cookiecutter-djangopackage.
help: ## Display this help message
	@echo "Please run \`make <target>\` where <target> is one of"
	@perl -nle'print $& if m{^[\.a-zA-Z_-]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

debug: ## Run and attach to container for debugging
	docker run -it --privileged --env-file .docker/env rlucioni/courtbot

image: ## Build an rlucioni/courtbot image
	docker build -t rlucioni/courtbot:latest .

logs: ## Tail a running container's logs
	docker logs -f courtbot

prune: ## Delete stopped containers and dangling images
	docker system prune -f

pull: ## Update the rlucioni/courtbot image
	docker pull rlucioni/courtbot

push: ## Push the rlucioni/courtbot image to Docker Hub
	docker push rlucioni/courtbot

run: ## Start a container derived from the rlucioni/courtbot image
	docker run -d --privileged --name courtbot --env-file .docker/env --restart on-failure rlucioni/courtbot

shell: ## Open a shell on a courtbot container
	docker run -it --privileged rlucioni/courtbot:latest /usr/bin/env bash

stop: ## Stop a running container
	docker stop courtbot
