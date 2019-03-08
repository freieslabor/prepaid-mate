|python3.5| |python3.6| |python3.7| |build-status| |lgtm-alerts| |lgtm-grade|

Prepaid Mate
============

Tired of fishing cash out of your pockets? Regardless of whether you pronounce
it [ˈpriːpɛɪ̯t ˈmaːtə] or [ˈpriːpɛɪ̯t meɪt], paying for drinks was never easier!

Put a fistful of dollars in the piggy bank and add the amount using any
computer or smartphone to your account. Thirsty? Start scanning! Identify
yourself with your personal RFID token (or barcode) and scan the barcode on the
drink. Cheers!

Required Hardware
=================

* some (embedded) computer running the software
* USB HID barcode scanner
* optional: USB HID RFID scanner
* optional: speakers for audio feedback

Software Components
===================

* flask server application providing a simple sqlite-backed API for
  - creating/modifying/viewing accounts
  - adding/view money (transactions)
  - performing payments
* scanner client listening to barcode/RFID events and triggering payments
* simple, static web frontend (currently in development)

Run it
======

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

Create a config file named `config`. Use `config.sample` as a starting point.

Now start the development server:

.. code-block:: bash

    (prepaid-drinks-venv) $ flask run

Or start the development server in debug mode:

.. code-block:: bash

    (prepaid-drinks-venv) $ FLASK_DEBUG=1 flask run

Now head your browser to `http://localhost:5000/static/index.html` to start.
Do not use the development server in a production environment.

In order to start the client:

.. code-block:: bash

    (prepaid-drinks-venv) $ python -m prepaid_mate.scanner_client

Test it
=======

Assuming you performed the steps above:

Activate your virtualenv one more time:

.. code-block:: bash

    $ source prepaid-drinks-venv/bin/activate

Now install the testing dependencies via pip inside the virtualenv:

.. code-block:: bash

    (prepaid-drinks-venv) $ pip install -r test-requirements.txt

Now run the test suite:

.. code-block:: bash

    (prepaid-drinks-venv) $ pytest -v

.. |python3.5| image:: https://img.shields.io/badge/python-3.5-blue.svg
    :alt: Supports python3.5
    :target: https://travis-ci.com/freieslabor/prepaid-mate

.. |python3.6| image:: https://img.shields.io/badge/python-3.6-blue.svg
    :alt: Supports python3.6
    :target: https://travis-ci.com/freieslabor/prepaid-mate

.. |python3.7| image:: https://img.shields.io/badge/python-3.7-blue.svg
    :alt: Supports python3.7
    :target: https://travis-ci.com/freieslabor/prepaid-mate

.. |build-status| image:: https://travis-ci.com/freieslabor/prepaid-mate.svg?branch=master
    :alt: Travis build status
    :target: https://travis-ci.com/freieslabor/prepaid-mate

.. |lgtm-alerts| image:: https://img.shields.io/lgtm/alerts/g/freieslabor/prepaid-mate.svg?logo=lgtm&logoWidth=18
    :alt: Total lgtm alerts
    :target: https://lgtm.com/projects/g/freieslabor/prepaid-mate/alerts/

.. |lgtm-grade| image:: https://img.shields.io/lgtm/grade/python/g/freieslabor/prepaid-mate.svg?logo=lgtm&logoWidth=18
    :alt: Language grade: Python
    :target: https://lgtm.com/projects/g/freieslabor/prepaid-mate/context:python
