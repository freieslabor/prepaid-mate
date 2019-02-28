import copy
import json

import pytest
import requests


def test_payment_perform_good(flask_server, create_account_with_balance):
    config = flask_server
    account_data = create_account_with_balance(100)
    drink_barcode = '4029764001807'
    payment_data = {
        'superuserpassword': config['DEFAULT']['superuser-password'],
        'account_barcode': account_data['barcode'],
        'drink_barcode': drink_barcode
    }

    r = requests.post('{}/payment/perform'.format(pytest.API_URL), data=payment_data)
    assert r.content == b'0'
    assert r.status_code == 200

    r = requests.post('{}/account/view'.format(pytest.API_URL), data=account_data)
    assert r.status_code == 200
    account_balance = json.loads(r.content.decode('utf-8'))[2]
    assert account_balance == 0

def test_payment_perform_wrong_pw(flask_server, create_account_with_balance):
    config = flask_server
    account_data = create_account_with_balance(100)
    drink_barcode = '4029764001807'
    payment_data = {
        'superuserpassword': 'some-madeup=pw',
        'account_barcode': account_data['barcode'],
        'drink_barcode': drink_barcode
    }

    r = requests.post('{}/payment/perform'.format(pytest.API_URL), data=payment_data)
    assert r.content == b'Wrong superuserpassword'
    assert r.status_code == 400

    r = requests.post('{}/account/view'.format(pytest.API_URL), data=account_data)
    assert r.status_code == 200
    account_balance = json.loads(r.content.decode('utf-8'))[2]
    assert account_balance == account_data['money']

def test_payment_perform_insufficient_funds(flask_server, create_account_with_balance):
    config = flask_server
    account_data = create_account_with_balance(100)
    drink_barcode = '4029764001807'
    payment_data = {
        'superuserpassword': config['DEFAULT']['superuser-password'],
        'account_barcode': account_data['barcode'],
        'drink_barcode': drink_barcode
    }

    r = requests.post('{}/payment/perform'.format(pytest.API_URL), data=payment_data)
    assert r.content == b'0'
    assert r.status_code == 200

    r = requests.post('{}/payment/perform'.format(pytest.API_URL), data=payment_data)
    assert r.content == b'Insufficient funds'
    assert r.status_code == 400

    r = requests.post('{}/account/view'.format(pytest.API_URL), data=account_data)
    assert r.status_code == 200
    account_balance = json.loads(r.content.decode('utf-8'))[2]
    assert account_balance == 0
