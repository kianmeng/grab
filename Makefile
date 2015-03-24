flake:
	flake8 grab test setup.py

flake_verbose:
	flake8 grab test setup.py --show-pep8

test:
	tox -e py27

test_all:
	tox -e py27-all,py34-all

coverage:
	coverage erase
	coverage run --source=grab ./runtest.py --test-all
	coverage report -m

coverage_full:
	coverage erase
	coverage run --source=grab ./runtest.py --test-all --extra --backend-mongo --backend-mysql --backend-redis --backend-postgres
	coverage report -m

coverage_missing:
	coverage erase
	coverage run --source=grab ./runtest.py --test-all --extra --backend-mongo --backend-mysql --backend-redis --backend-postgres
	coverage report -m | grep -v '100%' | grep -v Missing | grep -v -- '----' | sort -k 3 -nr

clean:
	find -name '*.pyc' -delete
	find -name '*.swp' -delete

.PHONY: all build venv flake test vtest testloop cov clean doc
