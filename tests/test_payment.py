"""Tests /api/payment/perform API call."""
# disable unused arguments used to run fixtures
# pylint: disable=unused-argument

import json

import pytest
import requests

API_URL = pytest.API_URL  # pylint: disable=no-member

def test_payment_perform_good(flask_server, create_account_with_balance):
    """Test if payments work."""
    config = flask_server
    account_data = create_account_with_balance(100)
    drink_barcode = '4029764001807'
    payment_data = {
        'superuserpassword': config['DEFAULT']['superuser-password'],
        'account_code': account_data['code'],
        'drink_barcode': drink_barcode
    }

    req = requests.post('{}/payment/perform'.format(API_URL), data=payment_data)
    assert req.content == b'0'
    assert req.status_code == 200

    req = requests.post('{}/account/view'.format(API_URL), data=account_data)
    assert req.status_code == 200
    account_balance = json.loads(req.content.decode('utf-8'))[2]
    assert account_balance == 0

def test_payment_perform_wrong_pw(flask_server, create_account_with_balance):
    """Test if payment with wrong password fails as expected."""
    account_data = create_account_with_balance(100)
    drink_barcode = '4029764001807'
    payment_data = {
        'superuserpassword': 'some-madeup=pw',
        'account_code': account_data['code'],
        'drink_barcode': drink_barcode
    }

    req = requests.post('{}/payment/perform'.format(API_URL), data=payment_data)
    assert req.content == b'Wrong superuserpassword'
    assert req.status_code == 400

    req = requests.post('{}/account/view'.format(API_URL), data=account_data)
    assert req.status_code == 200
    account_balance = json.loads(req.content.decode('utf-8'))[2]
    assert account_balance == account_data['money']

def test_payment_perform_insufficient_funds(flask_server, create_account_with_balance):
    """
    Test if payments for accounts with insufficient funds fails as expected.
    """
    config = flask_server
    account_data = create_account_with_balance(100)
    drink_barcode = '4029764001807'
    payment_data = {
        'superuserpassword': config['DEFAULT']['superuser-password'],
        'account_code': account_data['code'],
        'drink_barcode': drink_barcode
    }

    req = requests.post('{}/payment/perform'.format(API_URL), data=payment_data)
    assert req.content == b'0'
    assert req.status_code == 200

    req = requests.post('{}/payment/perform'.format(API_URL), data=payment_data)
    assert req.content == b'Insufficient funds'
    assert req.status_code == 400

    req = requests.post('{}/account/view'.format(API_URL), data=account_data)
    assert req.status_code == 200
    account_balance = json.loads(req.content.decode('utf-8'))[2]
    assert account_balance == 0
