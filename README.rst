|build-status|

Getting started
===============

Assuming you're running Debian (or Ubuntu) and want to use a virtualenv:

.. code-block:: bash

    $ apt-get install python3 python3-virtualenv python3-pip virtualenv

Create the virtualenv and activate it:

.. code-block:: bash

    $ virtualenv -p python3 prepaid-drinks-venv
    $ source prepaid-drinks-venv/bin/activate

Now install the Python dependencies via pip inside the virtualenv:

.. code-block:: bash

    (prepaid-drinks-venv) $ pip install -r requirements.txt

Create a config file named `config`.
See `config.sample` for an example config.

Now start the development server:

.. code-block:: bash

    $ flask run

Or start the development server in debug mode:

.. code-block:: bash

    $ FLASK_DEBUG=1 flask run

Now head your browser to `http://localhost:5000/` to start.
Do not use the development server in a production environment.

.. |build-status| image:: https://travis-ci.com/freieslabor/prepaid-mate.svg?branch=bst%2Fdev
    :target: https://travis-ci.com/freieslabor/prepaid-mate
