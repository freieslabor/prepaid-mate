import pytest
import requests


def test_account_creation_good(flask_server):
    r = requests.post('{}/account/create'.format(pytest.API_URL),
                      data={'name': 'foo', 'password':'bar', 'barcode': '123'})
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

def test_account_modification_good(flask_server, create_account):
    data = create_account
    data['new_name'] = 'foo2'
    data['new_password'] = 'bar2'
    data['new_barcode'] = '456'

    r = requests.post('{}/account/modify'.format(pytest.API_URL), data=data)
    assert r.status_code == 200
    assert r.content == b'ok'
