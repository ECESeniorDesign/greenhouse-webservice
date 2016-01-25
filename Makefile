.PHONY: install db

install: requirements.txt
	pip install -r requirements.txt

db:
	python setup.py db

server:
	python setup.py server

console:
	python -i setup.py console
