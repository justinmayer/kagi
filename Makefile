VIRTUALENV = virtualenv --python=python3
VENV := $(shell echo $${VIRTUAL_ENV-.venv} | xargs realpath)
PYTHON = $(VENV)/bin/python
INSTALL_STAMP = $(VENV)/.install.stamp
POETRY := $(shell which poetry .venv/bin/poetry)
PRECOMMIT := $(shell which pre-commit .venv/bin/pre-commit)
PRECOMMIT_HOOK := .git/hooks/pre-commit

all: install
install: $(INSTALL_STAMP) $(PRECOMMIT_HOOK)
$(INSTALL_STAMP): $(PYTHON) pyproject.toml
	$(VENV)/bin/pip install -U pip
	POETRY=$$(which "poetry" ".venv/bin/poetry" | head -n1); $$POETRY install || $$POETRY update
	touch $(INSTALL_STAMP)

# Look for poetry in the path
poetry:
ifndef POETRY
# Install poetry in the virtualenv only if missing
	$(VENV)/bin/pip install poetry
endif

$(PRECOMMIT_HOOK):
ifndef PRECOMMIT
# Install pre-commit in the virtualenv only if missing
	$(VENV)/bin/pip install pre-commit
endif
	$$(which "pre-commit" ".venv/bin/pre-commit" | head -n1) install

virtualenv: $(PYTHON)
$(PYTHON):
	$(VIRTUALENV) $(VENV)

serve: $(INSTALL_STAMP)
	cd testproj; $(PYTHON) manage.py runserver_plus \
        --cert-file $(VENV)/localhost.crt \
        --key-file $(VENV)/localhost.key

tests: $(INSTALL_STAMP)
	$(VENV)/bin/pytest -s --doctest-modules --cov-report term-missing --cov-fail-under 100 --cov kagi

makemigrations:
	cd testproj; $(PYTHON) manage.py makemigrations

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
