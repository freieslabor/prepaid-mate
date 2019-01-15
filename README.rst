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

    $ ./server.py

Now head your browser to `http://localhost:8888/` to start.
