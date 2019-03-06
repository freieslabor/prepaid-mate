"""Tests /api/money/* API calls."""
# disable unused arguments used to run fixtures
# pylint: disable=unused-argument

import pytest

API_URL = pytest.API_URL  # pylint: disable=no-member

def test_money_add_view_account_view_good(flask_server, create_account):
    """
    Test if adding money and view transactions and view account info after.
    """
    import copy
    import time
    import json
    import requests

    data = create_account
    data_add = copy.copy(data)
    data_add['money'] = 1000

    req = requests.post('{}/money/add'.format(API_URL), data=data_add)
    assert req.status_code == 200
    assert req.content == b'ok'

    req = requests.post('{}/money/view'.format(API_URL), data=data)
    assert req.status_code == 200
    result = json.loads(req.content.decode('utf-8'))
    assert len(result) == 1
    assert result[0][:2] == [1000, "Guthaben aufgeladen"]
    assert isinstance(result[0][2], int)
    assert 0 < result[0][2] < time.time()

    req = requests.post('{}/account/view'.format(API_URL), data=data)
    assert req.status_code == 200
    assert json.loads(req.content.decode('utf-8')) == [data['name'], data['code'],
                                                       data_add['money']]

def test_money_add_incomplete(flask_server, create_account):
    """Test if adding money with incomplete parameters fails as expected."""
    import copy
    import json
    import requests

    data = create_account
    data['money'] = 1000

    remove_inputs = ['name', 'password', 'money']

    for remove_input in remove_inputs:
        data_tmp = copy.copy(data)
        del data_tmp[remove_input]

        req = requests.post('{}/money/add'.format(API_URL), data=data_tmp)
        assert req.status_code == 400
        assert req.content != b'ok'

        req = requests.post('{}/money/view'.format(API_URL), data=data)
        assert req.status_code == 200
        assert json.loads(req.content.decode('utf-8')) == []

def test_money_add_empty(flask_server, create_account):
    """Test if adding money with empty parameters fails as expected."""
    import copy
    import json
    import requests

    data = create_account
    data['money'] = 1000

    empty_inputs = ['name', 'password', 'money']

    for empty_input in empty_inputs:
        data_tmp = copy.copy(data)
        data_tmp[empty_input] = ''

        req = requests.post('{}/money/add'.format(API_URL), data=data_tmp)
        assert req.status_code == 400
        assert req.content != b'ok'

        req = requests.post('{}/money/view'.format(API_URL), data=data)
        assert req.status_code == 200
        assert json.loads(req.content.decode('utf-8')) == []

def test_money_add_negative(flask_server, create_account):
    """Test if adding negative amounts of money fails as expected."""
    import json
    import requests

    data = create_account
    data['money'] = -1000

    req = requests.post('{}/money/add'.format(API_URL), data=data)
    assert req.status_code == 400
    assert req.content == b'Zero/negative money given'

    req = requests.post('{}/money/view'.format(API_URL), data=data)
    assert req.status_code == 200
    assert json.loads(req.content.decode('utf-8')) == []

def test_money_add_nonumber(flask_server, create_account):
    """
    Test if adding strings that are not numbers as money fails as expected.
    """
    import json
    import requests

    data = create_account
    money_inputs = ['a', '0x100', '!200']
    for money_input in money_inputs:
        data['money'] = money_input

        req = requests.post('{}/money/add'.format(API_URL), data=data)
        assert req.status_code == 400
        assert req.content == b'Money must be specified in cents'

        req = requests.post('{}/money/view'.format(API_URL), data=data)
        assert req.status_code == 200
        assert json.loads(req.content.decode('utf-8')) == []

def test_money_view_incomplete(flask_server, create_account):
    """Test if money view with incomplete parameters fails as expected."""
    import copy
    import requests

    data = create_account

    remove_inputs = ['name', 'password']

    for remove_input in remove_inputs:
        data_tmp = copy.copy(data)
        del data_tmp[remove_input]

        req = requests.post('{}/money/view'.format(API_URL), data=data_tmp)
        assert req.status_code == 400
        assert req.content == b'Incomplete request'

def test_money_view_empty(flask_server, create_account):
    """Test if money view with empty parameters fails as expected."""
    import copy
    import requests

    data = create_account

    empty_inputs = ['name', 'password']

    for empty_input in empty_inputs:
        data_tmp = copy.copy(data)
        data_tmp[empty_input] = ''

        req = requests.post('{}/money/view'.format(API_URL), data=data_tmp)
        assert req.status_code == 400
        assert req.content in (b'No such account in database', b'Wrong password')
