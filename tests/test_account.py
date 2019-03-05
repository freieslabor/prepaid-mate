"""Tests /api/account/* API calls."""
# disable unused arguments used to run fixtures
# pylint: disable=unused-argument

import copy
import json

import pytest
import requests

API_URL = pytest.API_URL  # pylint: disable=no-member

def test_account_creation_good(flask_server):
    """Test if account creation works."""
    req = requests.post('{}/account/create'.format(API_URL),
                        data={'name': 'foo', 'password': 'bar', 'code': '123'})
    assert req.status_code == 200
    assert req.content == b'ok'

def test_account_creation_incomplete(flask_server):
    """Test if incomplete account creation fails as expected."""
    datas = (
        {'password': 'bar', 'code': '123'},
        {'name': 'foo', 'code': '123'},
        {'name': 'foo', 'password': 'bar'},
        {'password': 'bar', 'code': '123'},
        {'name': 'foo', 'code': '123'},
        {'name': 'foo'},
        {'password': 'bar'},
        {'code': '123'},
    )

    for data in datas:
        req = requests.post('{}/account/create'.format(API_URL), data=data)
        assert req.status_code == 400
        assert req.content == b'Incomplete request'

def test_account_creation_empty(flask_server):
    """Test if account creation with empty string for parameter fails as expected."""
    datas = (
        {'name': '', 'password': 'bar', 'code': '123'},
        {'name': 'foo', 'password': '', 'code': '123'},
        {'name': 'foo', 'password': 'bar', 'code': ''},
    )

    for data in datas:
        req = requests.post('{}/account/create'.format(API_URL), data=data)
        assert req.status_code == 400
        assert req.content == b'Incomplete request'

def test_account_modification_good(flask_server, create_account):
    """Test if account modification works."""
    data = create_account
    data['new_name'] = 'foo2'
    data['new_password'] = 'bar2'
    data['new_code'] = '456'

    req = requests.post('{}/account/modify'.format(API_URL), data=data)
    assert req.status_code == 200
    assert req.content == b'ok'

def test_account_modification_inexistent(flask_server):
    """Test account modification of inexistent account."""
    data = {
        'name': 'no',
        'password': 'nope',
        'new_name': 'foo2',
        'new_password': 'bar2',
        'new_code': '456',
    }

    req = requests.post('{}/account/modify'.format(API_URL), data=data)
    assert req.status_code == 400
    assert req.content == b'No such account in database'

def test_account_modification_empty(flask_server, create_account):
    """Test account modification with empty string for parameter fails as expected."""
    data = create_account
    inputs = (
        {'new_name': '', 'new_password': 'bar2', 'new_code': '456'},
        {'new_name': 'foo2', 'new_password': '', 'new_code': '456'},
        {'new_name': 'foo2', 'new_password': 'bar2', 'new_code': ''},
    )
    for input_ in inputs:
        data_tmp = copy.copy(data)
        data_tmp = {**data_tmp, **input_}

        req = requests.post('{}/account/modify'.format(API_URL), data=data_tmp)
        assert req.status_code == 400
        assert req.content == b'Incomplete request'

def test_account_modification_incomplete(flask_server, create_account):
    """Test if incomplete account modification fails as expected."""
    data = create_account
    inputs = (
        {'new_password': 'bar2', 'new_code': '456'},
        {'new_name': 'foo2', 'new_code': '456'},
        {'new_name': 'foo2', 'new_password': 'bar2'},
        {'new_password': 'bar2', 'new_code': '456'},
        {'new_name': 'foo2', 'new_code': '456'},
        {'new_name': 'foo2'},
        {'new_password': 'bar2'},
        {'new_code': '456'},

    )
    for input_ in inputs:
        data_tmp = copy.copy(data)
        data_tmp = {**data_tmp, **input_}

        req = requests.post('{}/account/modify'.format(API_URL), data=data_tmp)
        assert req.status_code == 400
        assert req.content == b'Incomplete request'

def test_account_view_good(flask_server, create_account):
    """Test if account view works."""
    data = create_account

    req = requests.post('{}/account/view'.format(API_URL), data=data)
    assert req.status_code == 200
    assert json.loads(req.content.decode('utf-8')) == [data['name'], data['code'], 0]

def test_account_view_wrong_pw(flask_server, create_account):
    """Test if account view with wrong pw fails as expected."""
    data = create_account
    data['password'] += '123'

    req = requests.post('{}/account/view'.format(API_URL), data=data)
    assert req.status_code == 400
    assert req.content == b'Wrong password'

def test_account_view_inexistent_account(flask_server, create_account):
    """Test if account view for inexistent account fails as expected."""
    data = create_account
    data['name'] += '123'

    req = requests.post('{}/account/view'.format(API_URL), data=data)
    assert req.status_code == 400
    assert req.content == b'No such account in database'
