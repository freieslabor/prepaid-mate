SHELL=/bin/bash
PYTHON=python3

PYTHON_ENV_ROOT=envs
PYTHON_DEV_ENV=$(PYTHON_ENV_ROOT)/$(PYTHON)-dev
PYTHON_TEST_ENV=$(PYTHON_ENV_ROOT)/$(PYTHON)-test


.PHONY: all distclean test server

all: server

# helper ######################################################################
distclean:
	rm -rf $(PYTHON_ENV_ROOT)

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

config:
	cp config.sample config

# targets #####################################################################
test: | $(PYTHON_TEST_ENV)
	. $(PYTHON_TEST_ENV)/bin/activate && \
	pytest -v $(args)

server: | config $(PYTHON_DEV_ENV)
	. $(PYTHON_DEV_ENV)/bin/activate && \
	flask run $(args)
