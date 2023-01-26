SHELL=/bin/bash
PYTHON=python3

PYTHON_ENV_ROOT=envs
PYTHON_DEV_ENV=$(PYTHON_ENV_ROOT)/$(PYTHON)-dev
PYTHON_TEST_ENV=$(PYTHON_ENV_ROOT)/$(PYTHON)-test

HOST=localhost
PORT=5000
SHELL_SERVER_URL=file://socket


.PHONY: all distclean test server server-shell migrate collectstatic superuser

all: server

# helper ######################################################################
distclean:
	rm -rf prepaid_mate/static/django
	rm -rf $(PYTHON_ENV_ROOT)

migrate: | $(PYTHON_DEV_ENV)
	. $(PYTHON_DEV_ENV)/bin/activate && \
	prepaid-mate-manage-django migrate $(args)

collectstatic: | $(PYTHON_DEV_ENV)
	. $(PYTHON_DEV_ENV)/bin/activate && \
	prepaid-mate-manage-django collectstatic $(args)

superuser: | $(PYTHON_DEV_ENV)
	. $(PYTHON_DEV_ENV)/bin/activate && \
	prepaid-mate-manage-django createsuperuser $(args)

# prequisits ##################################################################
$(PYTHON_DEV_ENV): requirements.txt
	rm -rf $(PYTHON_DEV_ENV) && \
	$(PYTHON) -m venv $(PYTHON_DEV_ENV) && \
	. $(PYTHON_DEV_ENV)/bin/activate && \
	pip install pip --upgrade && \
	pip install -r ./requirements.txt

$(PYTHON_TEST_ENV): test-requirements.txt
	rm -rf $(PYTHON_TEST_ENV) && \
	$(PYTHON) -m venv $(PYTHON_TEST_ENV) && \
	. $(PYTHON_TEST_ENV)/bin/activate && \
	pip install pip --upgrade && \
	pip install -r ./test-requirements.txt

prepaid_mate/static/django: | $(PYTHON_DEV_ENV)
	. $(PYTHON_DEV_ENV)/bin/activate && \
	prepaid-mate-manage-django collectstatic

config:
	cp config.sample config

# targets #####################################################################
test: | $(PYTHON_TEST_ENV)
	. $(PYTHON_TEST_ENV)/bin/activate && \
	pytest -v $(args)

server: | config $(PYTHON_DEV_ENV) prepaid_mate/static/django
	. $(PYTHON_DEV_ENV)/bin/activate && \
	lona run-server \
		--project-root=prepaid_mate \
		--settings settings.py \
		--host=$(HOST) \
		--port=$(PORT) \
		--shell-server-url=$(SHELL_SERVER_URL) \
		$(args)

server-shell: | $(PYTHON_DEV_ENV)
	. $(PYTHON_DEV_ENV)/bin/activate && \
	rlpython $(SHELL_SERVER_URL) $(args)
