.DEFAULT_GOAL := help
.PHONY: requirements

deploy: ## package and deploy
	zappa deploy prod

# generates a help message. Borrowed from https://github.com/pydanny/cookiecutter-djangopackage.
help: ## display this help message
	@echo "Run \`make <target>\` where <target> is one of"
	@perl -nle'print $& if m{^[\.a-zA-Z_-]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

lint: ## run flake8
	flake8 courtbot.py

package: ## package app without deploying
	zappa package prod

requirements: ## install requirements
	pip install -r requirements.txt

rollback: ## rollback code to previously deployed version
	zappa rollback prod -n 1

schedule: ## schedule functions to run at regular intervals
	zappa schedule prod

serve: ## run the Flask app locally, without Lambda
	FLASK_APP=courtbot.py FLASK_DEBUG=1 flask run

status: ## view deployment status
	zappa status prod

tail: ## watch deployment logs for the last hour
	zappa tail prod --since 1h

tunnel: ## use ngrok to expose a local server to the Internet
	ngrok http 5000

undeploy: ## remove API Gateway routes, Lambda function, and CloudWatch logs
	zappa undeploy prod --remove-logs

unschedule: ## cancel scheduled functions
	zappa unschedule prod

update: ## upload new Python code without touching API Gateway routes
	zappa update prod
