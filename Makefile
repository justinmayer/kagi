VIRTUALENV = virtualenv --python=python3
VENV := $(shell echo $${VIRTUAL_ENV-.venv} | xargs realpath)
PYTHON = $(VENV)/bin/python
INSTALL_STAMP = $(VENV)/.install.stamp


all: install
install: $(INSTALL_STAMP)
$(INSTALL_STAMP): $(PYTHON) pyproject.toml
	$(VENV)/bin/pip install -U poetry
	$(VENV)/bin/poetry install
	$(VENV)/bin/poetry update
	touch $(INSTALL_STAMP)

virtualenv: $(PYTHON)
$(PYTHON):
	$(VIRTUALENV) $(VENV)

serve: $(INSTALL_STAMP)
	cd testproj; $(PYTHON) manage.py runserver_plus \
        --cert-file $(VENV)/localhost.crt \
        --key-file $(VENV)/localhost.key

tests: $(INSTALL_STAMP)
	$(VENV)/bin/pytest -s

migrate:
	cd testproj; $(PYTHON) manage.py migrate
