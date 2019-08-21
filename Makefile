VIRTUALENV = virtualenv --python=python3
VENV := $(shell echo $${VIRTUAL_ENV-.venv} | xargs realpath)
PYTHON = $(VENV)/bin/python
INSTALL_STAMP = $(VENV)/.install.stamp
POETRY := $(shell which poetry)
PRECOMMIT := $(shell which pre-commit)
PRECOMMIT_HOOK := .git/hooks/pre-commit

all: install
install: $(INSTALL_STAMP) $(PRECOMMIT_HOOK)
$(INSTALL_STAMP): $(PYTHON) poetry pyproject.toml
	$(VENV)/bin/pip install -U pip
	POETRY=$$(which poetry .venv/bin/poetry); $$POETRY install || $$POETRY update
	touch $(INSTALL_STAMP)

# Look for poetry in the path
poetry:
ifndef POETRY
# Install it in the virtualenv if missing
	$(VENV)/bin/pip install poetry
endif

# Look for pre-commit in the path
pre-commit:
ifndef PRECOMMIT
# Install it in the virtualenv if missing
	$(VENV)/bin/pip install pre-commit
endif

$(PRECOMMIT_HOOK): pre-commit
	$$(which pre-commit .venv/bin/pre-commit) install

virtualenv: $(PYTHON)
$(PYTHON):
	$(VIRTUALENV) $(VENV)

serve: $(INSTALL_STAMP)
	cd testproj; $(PYTHON) manage.py runserver_plus \
        --cert-file $(VENV)/localhost.crt \
        --key-file $(VENV)/localhost.key

tests: $(INSTALL_STAMP)
	$(VENV)/bin/pytest -s --doctest-modules --cov-report term-missing --cov-fail-under 100 --cov kagi

migrate:
	cd testproj; $(PYTHON) manage.py migrate

black: $(INSTALL_STAMP)
	$(VENV)/bin/black kagi testproj

isort: $(INSTALL_STAMP)
	$(VENV)/bin/isort --recursive .isort.cfg kagi/* testproj/*

flake8: $(INSTALL_STAMP)
	$(VENV)/bin/flake8 kagi testproj

lint: $(INSTALL_STAMP)
	$(VENV)/bin/isort -c --recursive .isort.cfg kagi/* testproj/*
	$(VENV)/bin/black --check kagi testproj
	$(VENV)/bin/flake8 kagi testproj
