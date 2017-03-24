.PHONY: create image kill logs provision prune pull push quality run shell stop

create: ## Create a Droplet for hosting courtbot
	docker-machine create --driver digitalocean --digitalocean-access-token $$(cat ~/.digitalocean-access-token) courtbot

image: ## Build an rlucioni/courtbot image
	docker build -t rlucioni/courtbot:latest .

kill: ## Stop and remove the Droplet hosting courtbot.
	docker-machine stop courtbot && docker-machine rm courtbot

logs: ## Tail a running container's logs
	docker logs -f courtbot

provision: ## Reprovision an existing courtbot machine
	docker-machine provision courtbot

prune: ## Delete stopped containers and dangling images
	docker system prune

pull: ## Update the rlucioni/courtbot image
	docker pull rlucioni/courtbot

push: ## Push the rlucioni/courtbot image to Docker Hub
	docker push rlucioni/courtbot

quality: ## Run quality checks
	docker run rlucioni/courtbot flake8

run: ## Start a container derived from the rlucioni/courtbot image
	docker run -d --name courtbot --env-file .docker/env --restart on-failure rlucioni/courtbot

shell: ## Open a shell on a running container
	docker exec -it courtbot /usr/bin/env bash

stop: ## Stop a running container
	docker stop courtbot
