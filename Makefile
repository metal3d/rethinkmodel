.PHONY:doc
TEST_FILTER=""

test:
	rm -rf cover && mkdir cover
	pipenv run nosetests -sv --with-coverage --cover-package=rethinkmodel --cover-html $(TEST_FILTER)

build: clean
	pipenv run python -m pep517.build .


clean-all: clean-doc

doc:
	cd doc && pipenv run make html

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
