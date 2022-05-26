"""Test scanner_client.py with flask server."""
# disable unused arguments used to run fixtures
# pylint: disable=unused-argument

import re

import pytest

def get_log_line(proc, logger='.*:root:'):
    for line in iter(proc.stderr.readline, ''):
        line = line.decode('utf-8')
        if re.search(logger, line):
            return line

    return None


def test_client_payment(flask_server, create_account_with_balance, create_drink, scanner_client):
    """Test payment on scanner_client.py with flask server and preset account."""
    data = create_account_with_balance(150)
    drink = create_drink
    proc = scanner_client()

    assert 'account code: {}'.format(data['code']) in get_log_line(proc)
    get_log_line(proc) # ignore user greeting

    # note that drink['barcode']) is in the umockdev recorded session being played back
    assert 'account "{}" ordered "{}"'.format(data['code'], drink['barcode']) in get_log_line(proc)
    assert 'calling API with' in get_log_line(proc)
    assert 'callback successful: ' in get_log_line(proc)
