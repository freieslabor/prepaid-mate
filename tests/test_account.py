"""Tests /api/account/* API calls."""
# disable unused arguments used to run fixtures
# pylint: disable=unused-argument
import pytest

API_URL = pytest.API_URL  # pylint: disable=no-member

def test_account_creation_good(flask_server):
    """Test if account creation works."""
    import requests

    req = requests.post('{}/account/create'.format(API_URL),
                        data={'name': 'foo', 'password': 'bar', 'code': '123'})
    assert req.status_code == 200
    assert req.content == b'ok'

def test_account_creation_incomplete(flask_server):
    """Test if incomplete account creation fails as expected."""
    import requests

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
    import requests

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
    import requests

    data = create_account
    data['new_name'] = 'foo2'
    data['new_password'] = 'bar2'
    data['new_code'] = '456'

    req = requests.post('{}/account/modify'.format(API_URL), data=data)
    assert req.status_code == 200
    assert req.content == b'ok'

def test_account_modification_superuser_good(flask_server, create_account):
    """Test if account modification works."""
    import requests

    config = flask_server
    data = {
        'superuserpassword': config['DEFAULT']['superuser-password'],
        'name': create_account['name'],
        'new_name': 'foo2',
        'new_password': 'bar2',
        'new_code': '456',
    }

    req = requests.post('{}/account/modify'.format(API_URL), data=data)
    assert req.status_code == 200
    assert req.content == b'ok'

def test_account_modification_superuser_wrong_pw(flask_server, create_account):
    """Test if account modification works."""
    import requests

    config = flask_server
    data = {
        'superuserpassword': '123',
        'name': create_account['name'],
        'new_name': 'foo2',
        'new_password': 'bar2',
        'new_code': '456',
    }

    req = requests.post('{}/account/modify'.format(API_URL), data=data)
    assert req.status_code == 400
    assert req.content == b'Wrong superuserpassword'

def test_account_modification_inexistent(flask_server):
    """Test account modification of inexistent account."""
    import requests

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
    import copy
    import requests

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

def test_account_view_good(flask_server, create_account):
    """Test if account view works."""
    import json
    import requests

    data = create_account

    req = requests.post('{}/account/view'.format(API_URL), data=data)
    assert req.status_code == 200
    assert json.loads(req.content.decode('utf-8')) == [data['name'], data['code'], 0]

def test_account_view_wrong_pw(flask_server, create_account):
    """Test if account view with wrong pw fails as expected."""
    import requests

    data = create_account
    data['password'] += '123'

    req = requests.post('{}/account/view'.format(API_URL), data=data)
    assert req.status_code == 400
    assert req.content == b'Wrong password'

def test_account_view_inexistent_account(flask_server, create_account):
    """Test if account view for inexistent account fails as expected."""
    import requests

    data = create_account
    data['name'] += '123'

    req = requests.post('{}/account/view'.format(API_URL), data=data)
    assert req.status_code == 400
    assert req.content == b'No such account in database'

def test_account_code_exists(flask_server, create_account):
    """Test if account code verification method works with existing account."""
    import requests
    import json

    account = create_account
    data = {'code': account['code']}
    req = requests.post('{}/account/code_exists'.format(API_URL), data=data)
    status, name = json.loads(req.content.decode('utf-8'))
    assert status
    assert name is not None

    req = requests.get('{}/last_unknown_code'.format(API_URL))
    assert not req.content.decode('utf-8')

@pytest.mark.timeout(65)
def test_account_code_does_not_exist_60s(flask_server):
    """
    Test if account code verification method works with inexistent account and
    last unknown code can be retrieved within the following 60 seconds.
    """
    import requests
    import json
    import time

    data = {'code': '1234'}
    req = requests.post('{}/account/code_exists'.format(API_URL), data=data)
    status, name = json.loads(req.content.decode('utf-8'))
    assert not status
    assert name is None

    req = requests.get('{}/last_unknown_code'.format(API_URL))
    assert req.content.decode('utf-8') == data['code']

    time.sleep(60)

    # code should not be available anymore
    req = requests.get('{}/last_unknown_code'.format(API_URL))
    assert not req.content.decode('utf-8')
