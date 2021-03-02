.PHONY:doc
TEST_FILTER=""
NOW:=$(shell date +"%Y%m%d-%H%M%S")

test:
	rm -rf cover && mkdir cover
	pipenv run pytest --cov=rethinkmodel --cov-report=xml:./coverage-reports/coverage-$(NOW).xml -sv 

build: clean
	pipenv run python -m pep517.build .


clean-all: clean-doc

.ONESHELL:
doc:
	cd doc && pipenv run make html
	cd ..
	rm -rf docs/*
	cp -ra doc/_build/html/* docs/

clean-doc:
	cd doc && pipenv run make clean

clean:
	rm -rf cover .coverage build dist *.egg-info

.ONESHELL:
listen-doc:
	make clean-doc doc
	while true; do
		inotifywait -e modify -r doc/ rethinkmodel/ | grep -P ".rst|.py|.css" && $(MAKE) clean-doc doc
	done


deploy: build
	pipenv run python -m twine upload dist/*

