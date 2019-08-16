VIRTUALENV = virtualenv --python=python3
VENV := $(shell echo $${VIRTUAL_ENV-.venv} | xargs realpath)
PYTHON = $(VENV)/bin/python
INSTALL_STAMP = $(VENV)/.install.stamp


all: install
install: $(INSTALL_STAMP) therapist
$(INSTALL_STAMP): $(PYTHON) pyproject.toml
	$(VENV)/bin/pip install -U poetry
	$(VENV)/bin/poetry install || $(VENV)/bin/poetry update
	touch $(INSTALL_STAMP)

virtualenv: $(PYTHON)
$(PYTHON):
	$(VIRTUALENV) $(VENV)

therapist: .therapist.yml
	$(VENV)/bin/therapist install

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
