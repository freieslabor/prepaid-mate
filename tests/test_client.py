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

def test_client_drink_view(flask_server, create_drink, scanner_client):
    """Test drink view on scanner_client.py with flask server and preset drink."""
    order_recorded = '42254300'
    proc = scanner_client(enabled='barcode')
    drink = create_drink

    assert 'account code: {}'.format(drink['barcode']) in get_log_line(proc)

    # simplification: works only for drink price in whole numbers
    assert 'Enjoy a cool {}, only {} Euro'.format(drink['name'], drink['price']//100) in get_log_line(proc)
