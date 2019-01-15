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

Now start the server:

.. code-block:: bash

    $ flask run

Or start the server in debug mode:

.. code-block:: bash

    $ FLASK_DEBUG=1 flask run

Now head your browser to `http://localhost:5000/` to start.
