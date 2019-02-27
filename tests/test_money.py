import copy
import json
import time

import pytest
import requests


def test_money_add_view_account_view_good(flask_server, create_account):
    data = create_account
    data_add = copy.copy(data)
    data_add['money'] = 1000

    r = requests.post('{}/money/add'.format(pytest.API_URL), data=data_add)
    assert r.status_code == 200
    assert r.content == b'ok'

    r = requests.post('{}/money/view'.format(pytest.API_URL), data=data)
    assert r.status_code == 200
    result = json.loads(r.content)
    assert len(result) == 1
    assert result[0][:2] == [1000, "Guthaben aufgeladen"]
    assert isinstance(result[0][2], int)
    assert 0 < result[0][2] < time.time()

    r = requests.post('{}/account/view'.format(pytest.API_URL), data=data)
    assert r.status_code == 200
    assert json.loads(r.content) == [data['name'], data['barcode'], data_add['money']]

def test_money_add_incomplete(flask_server, create_account):
    data = create_account
    data['money'] = 1000

    remove_inputs = ['name', 'password', 'money']

    for remove_input in remove_inputs:
        data_tmp = copy.copy(data)
        del data_tmp[remove_input]

        r = requests.post('{}/money/add'.format(pytest.API_URL), data=data_tmp)
        assert r.status_code == 400
        assert r.content != b'ok'

        r = requests.post('{}/money/view'.format(pytest.API_URL), data=data)
        assert r.status_code == 200
        assert json.loads(r.content) == []

def test_money_add_empty(flask_server, create_account):
    data = create_account
    data['money'] = 1000

    empty_inputs = ['name', 'password', 'money']

    for empty_input in empty_inputs:
        data_tmp = copy.copy(data)
        data_tmp[empty_input] = ''

        r = requests.post('{}/money/add'.format(pytest.API_URL), data=data_tmp)
        assert r.status_code == 400
        assert r.content != b'ok'

        r = requests.post('{}/money/view'.format(pytest.API_URL), data=data)
        assert r.status_code == 200
        assert json.loads(r.content) == []

def test_money_add_negative(flask_server, create_account):
    data = create_account
    data['money'] = -1000

    r = requests.post('{}/money/add'.format(pytest.API_URL), data=data)
    assert r.status_code == 400
    assert r.content == b'Zero/negative money given'

    r = requests.post('{}/money/view'.format(pytest.API_URL), data=data)
    assert r.status_code == 200
    assert json.loads(r.content) == []

def test_money_add_nonumber(flask_server, create_account):
    data = create_account
    money_inputs = ['a', '0x100', '!200']
    for money_input in money_inputs:
        data['money'] = money_input

        r = requests.post('{}/money/add'.format(pytest.API_URL), data=data)
        assert r.status_code == 400
        assert r.content == b'Money must be specified in cents'

        r = requests.post('{}/money/view'.format(pytest.API_URL), data=data)
        assert r.status_code == 200
        assert json.loads(r.content) == []

def test_money_view_incomplete(flask_server, create_account):
    data = create_account

    remove_inputs = ['name', 'password']

    for remove_input in remove_inputs:
        data_tmp = copy.copy(data)
        del data_tmp[remove_input]

        r = requests.post('{}/money/view'.format(pytest.API_URL), data=data_tmp)
        assert r.status_code == 400
        assert r.content == b'Incomplete request'

def test_money_view_empty(flask_server, create_account):
    data = create_account

    empty_inputs = ['name', 'password']

    for empty_input in empty_inputs:
        data_tmp = copy.copy(data)
        data_tmp[empty_input] = ''

        r = requests.post('{}/money/view'.format(pytest.API_URL), data=data_tmp)
        assert r.status_code == 400
        assert r.content in (b'No such account in database', b'Wrong password')
