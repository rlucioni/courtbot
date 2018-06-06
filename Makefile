deploy:
	zappa deploy prod

lint:
	flake8 courtbot.py

package:
	zappa package prod

prune:
	python prune.py

requirements:
	pip install -r requirements.txt

rollback:
	zappa rollback prod -n 1

schedule:
	zappa schedule prod

ship: update prune

serve:
	FLASK_APP=courtbot.py FLASK_DEBUG=1 flask run

status:
	zappa status prod

tail:
	zappa tail prod --since 1h

tunnel:
	ngrok http 5000

undeploy:
	zappa undeploy prod --remove-logs

unschedule:
	zappa unschedule prod

update:
	zappa update prod
