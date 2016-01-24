.PHONY: install db

install: requirements.txt
	pip install -r requirements.txt

db:
	python setup.py db
