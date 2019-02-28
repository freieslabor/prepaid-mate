import copy
import json

import pytest
import requests


def test_account_creation_good(flask_server):
    r = requests.post('{}/account/create'.format(pytest.API_URL),
                      data={'name': 'foo', 'password': 'bar', 'barcode': '123'})
    assert r.status_code == 200
    assert r.content == b'ok'

def test_account_creation_incomplete(flask_server):
    datas = (
        {'password': 'bar', 'barcode': '123'},
        {'name': 'foo', 'barcode': '123'},
        {'name': 'foo', 'password': 'bar'},
        {'password': 'bar', 'barcode': '123'},
        {'name': 'foo', 'barcode': '123'},
        {'name': 'foo'},
        {'password': 'bar'},
        {'barcode': '123'},
    )

    for data in datas:
        r = requests.post('{}/account/create'.format(pytest.API_URL), data=data)
        assert r.status_code == 400
        assert r.content == b'Incomplete request'

def test_account_creation_empty(flask_server):
    datas = (
        {'name': '', 'password': 'bar', 'barcode': '123'},
        {'name': 'foo', 'password': '', 'barcode': '123'},
        {'name': 'foo', 'password': 'bar', 'barcode': ''},
    )

    for data in datas:
        r = requests.post('{}/account/create'.format(pytest.API_URL), data=data)
        assert r.status_code == 400
        assert r.content == b'Incomplete request'

def test_account_modification_good(flask_server, create_account):
    data = create_account
    data['new_name'] = 'foo2'
    data['new_password'] = 'bar2'
    data['new_barcode'] = '456'

    r = requests.post('{}/account/modify'.format(pytest.API_URL), data=data)
    assert r.status_code == 200
    assert r.content == b'ok'

def test_account_modification_inexistent(flask_server):
    data = {'name': 'no', 'password': 'nope', 'new_name': 'foo2', 'new_password': 'bar2', 'new_barcode': '456'}

    r = requests.post('{}/account/modify'.format(pytest.API_URL), data=data)
    assert r.status_code == 400
    assert r.content == b'No such account in database'

def test_account_modification_empty(flask_server, create_account):
    data = create_account
    inputs = (
        {'new_name': '', 'new_password': 'bar2', 'new_barcode': '456'},
        {'new_name': 'foo2', 'new_password': '', 'new_barcode': '456'},
        {'new_name': 'foo2', 'new_password': 'bar2', 'new_barcode': ''},
    )
    for input_ in inputs:
        data_tmp = copy.copy(data)
        data_tmp = {**data_tmp, **input_}

        r = requests.post('{}/account/modify'.format(pytest.API_URL), data=data_tmp)
        assert r.status_code == 400
        assert r.content == b'Incomplete request'

def test_account_modification_incomplete(flask_server, create_account):
    data = create_account
    inputs = (
        {'new_password': 'bar2', 'new_barcode': '456'},
        {'new_name': 'foo2', 'new_barcode': '456'},
        {'new_name': 'foo2', 'new_password': 'bar2'},
        {'new_password': 'bar2', 'new_barcode': '456'},
        {'new_name': 'foo2', 'new_barcode': '456'},
        {'new_name': 'foo2'},
        {'new_password': 'bar2'},
        {'new_barcode': '456'},

    )
    for input_ in inputs:
        data_tmp = copy.copy(data)
        data_tmp = {**data_tmp, **input_}

        r = requests.post('{}/account/modify'.format(pytest.API_URL), data=data_tmp)
        assert r.status_code == 400
        assert r.content == b'Incomplete request'

def test_account_view_good(flask_server, create_account):
    data = create_account

    r = requests.post('{}/account/view'.format(pytest.API_URL), data=data)
    assert r.status_code == 200
    assert json.loads(r.content.decode('utf-8')) == [data['name'], data['barcode'], 0]

def test_account_view_wrong_pw(flask_server, create_account):
    data = create_account
    data['password'] += '123'

    r = requests.post('{}/account/view'.format(pytest.API_URL), data=data)
    assert r.status_code == 400
    assert r.content == b'Wrong password'

def test_account_view_inexistent_user(flask_server, create_account):
    data = create_account
    data['name'] += '123'

    r = requests.post('{}/account/view'.format(pytest.API_URL), data=data)
    assert r.status_code == 400
    assert r.content == b'No such account in database'
