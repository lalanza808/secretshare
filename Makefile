setup:
	python3 -m venv .venv
	.venv/bin/pip install .

dev:
	FLASK_APP=secretshare/app.py FLASK_SECRETS=config.py FLASK_DEBUG=1 .venv/bin/flask run
