.DEFAULT_GOAL := help
.PHONY: requirements

deploy: ## Package and deploy
	zappa deploy prod

# Generates a help message. Borrowed from https://github.com/pydanny/cookiecutter-djangopackage.
help: ## Display this help message
	@echo "Please run \`make <target>\` where <target> is one of"
	@perl -nle'print $& if m{^[\.a-zA-Z_-]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

lint: ## Run flake8
	flake8 courtbot.py

package: ## Package app without deploying
	zappa package prod

requirements: ## Install requirements
	pip install -r requirements.txt

rollback: ## Rollback code to previously deployed version
	zappa rollback prod -n 1

serve: ## Run the Flask app locally, without Lambda
	FLASK_APP=courtbot.py FLASK_DEBUG=1 flask run

status: ## View deployment status
	zappa status prod

tail: ## Watch deployment logs for the last hour
	zappa tail prod --since 1h

tunnel: ## Use ngrok to expose a local server to the Internet
	ngrok http 5000

undeploy: ## Remove API Gateway routes, Lambda function, and CloudWatch logs
	zappa undeploy prod --remove-logs

update: ## Upload new Python code without touching API Gateway routes
	zappa update prod
