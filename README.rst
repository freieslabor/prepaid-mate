|python3.5| |python3.6| |python3.7| |build-status| |lgtm-alerts| |lgtm-grade-python| |lgtm-grade-javascript|

Prepaid Mate
============

Tired of fishing cash out of your pockets? Regardless of whether you pronounce
it [ˈpriːpɛɪ̯t ˈmaːtə] or [ˈpriːpɛɪ̯t meɪt], paying for drinks was never easier!

Put a fistful of dollars in the piggy bank and add the amount using any
computer or smartphone to your account. Thirsty? Start scanning! Identify
yourself with your personal RFID token (or barcode) and scan the barcode on the
drink. Cheers!

Table of contents
=================

* `Required Hardware <#required-hardware>`_
* `Software Components <#software-components>`_
* `Installation and Configuration <#installation-and-configuration>`_
* `Run it <#run-it>`_
* `Test it <#test-it>`_
* `Deploy it <#deploy-it>`_

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

Installation and configuration
==============================

Assuming you're running Debian (or Ubuntu) and want to use a virtualenv:

.. code-block:: bash

    $ apt-get install python3 python3-virtualenv python3-pip virtualenv espeak

Create the virtualenv and activate it:

.. code-block:: bash

    $ virtualenv -p python3 prepaid-mate-venv
    $ source prepaid-mate-venv/bin/activate

Now install the Python dependencies via pip inside the virtualenv:

.. code-block:: bash

    (prepaid-mate-venv) $ pip install -r requirements.txt

In order to install Prepaid Mate in editable (development) mode use:

.. code-block:: bash

    (prepaid-mate-venv) $ pip install -e .

Otherwise:

.. code-block:: bash

    (prepaid-mate-venv) $ pip install .

Create a config file named `config`. Use `config.sample` as a starting point.

Run it
======

Now start the development server:

.. code-block:: bash

    (prepaid-mate-venv) $ flask run

Or start the development server in debug mode:

.. code-block:: bash

    (prepaid-mate-venv) $ FLASK_DEBUG=1 flask run

Now head your browser to `http://localhost:5000/static/index.html` to start.
Do not use the development server in a production environment. See below how to
deploy Prepaid Mate.

In order to start the client:

.. code-block:: bash

    (prepaid-mate-venv) $ scanner-client

Test it
=======

Assuming you performed the steps above:

.. code-block:: bash

    $ apt-get install umockdev

Activate your virtualenv one more time:

.. code-block:: bash

    $ source prepaid-mate-venv/bin/activate

Now install the testing dependencies via pip inside the virtualenv:

.. code-block:: bash

    (prepaid-mate-venv) $ pip install -r test-requirements.txt

Now run the test suite:

.. code-block:: bash

    (prepaid-mate-venv) $ pytest -v

Deploy it
=========

.. code-block:: bash

    $ apt-get install nginx

Configurations for udev, gunicorn and nginx are located in deploy/. Adjust
path, user and group as needed and copy these files to their corresponding
location in your target filesystem.

Now enable the nginx site, enable the gunicorn service and (re)start the services:

.. code-block:: bash

    $ ln -s /etc/nginx/sites-available/prepaid_mate /etc/nginx/sites-enabled/prepaid_mate
    $ systemctl enable gunicorn.service
    $ systemctl enable scanner-client.service
    $ systemctl restart nginx.service gunicorn.service

Prepaid Mate should now respond at http://localhost/.

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

.. |lgtm-grade-python| image:: https://img.shields.io/lgtm/grade/python/g/freieslabor/prepaid-mate.svg?logo=lgtm&logoWidth=18
    :alt: Language grade: Python
    :target: https://lgtm.com/projects/g/freieslabor/prepaid-mate/context:python

.. |lgtm-grade-javascript| image:: https://img.shields.io/lgtm/grade/javascript/g/freieslabor/prepaid-mate.svg?logo=lgtm&logoWidth=18
    :alt: Language grade: Javascript
    :target: https://lgtm.com/projects/g/freieslabor/prepaid-mate/context:javascript
