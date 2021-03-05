.PHONY:doc
TEST_FILTER=""
NOW:=$(shell date +"%Y%m%d-%H%M%S")
TRAVIS=0

test:
ifeq ($(TRAVIS), 1)
	pipenv run pytest --cov=rethinkmodel --cov-report=xml:./coverage-reports/coverage.xml -v 
else
	pipenv run pytest --cov=rethinkmodel --cov-report=html:./coverage -sv $(TEST_FILTER)
endif

build: clean
	pipenv run python -m pep517.build .

clean-all: clean-doc

.ONESHELL:
doc:
	cd doc && pipenv run make html
	cd ..
	rm -rf docs/*
	cp -ra doc/_build/html/* docs/

.ONESHELL:
pdf-doc:
	cd doc && pipenv run make latex
	cd _build/latex && make; make


clean-doc:
	cd doc && pipenv run make clean

clean:
	rm -rf build dist *.egg-info

.ONESHELL:
listen-doc:
	make clean-doc doc
	while true; do
		inotifywait -e modify -r doc/ rethinkmodel/ | grep -P ".rst|.py|.css|.html" && $(MAKE) clean-doc doc
	done

deploy: build
	pipenv run python -m twine upload dist/*
