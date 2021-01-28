TEST_FILTER=""

test:
	rm -rf cover && mkdir cover
	pipenv run nosetests -sv --with-coverage --cover-package=rethinkmodel --cover-html $(TEST_FILTER)

build: clean
	pipenv run python -m pep517.build .

clean:
	rm -rf cover .coverage build dist *.egg-info
