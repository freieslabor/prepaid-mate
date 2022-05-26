"""Tests /api/drink/* API calls."""
# disable unused arguments used to run fixtures
# pylint: disable=unused-argument
import pytest

API_URL = pytest.API_URL  # pylint: disable=no-member

def test_drink_creation_good(flask_server):
    """Test if drink creation works."""
    import requests

    config = flask_server
    data = {
        'superuserpassword': config['DEFAULT']['superuser-password'],
        'name': 'foo',
        'content_ml': 500,
        'price': 100,
        'barcode': '123'}

    req = requests.post('{}/drink/create'.format(API_URL), data=data)
    assert req.content == b'ok'
    req.raise_for_status()

def test_drink_creation_incomplete(flask_server):
    """Test if incomplete drink creation fails as expected."""
    import requests

    config = flask_server
    datas = (
        {'content_ml': 500, 'price': 100, 'barcode': '123'},
        {'name': 'foo', 'price': 100, 'barcode': '123'},
        {'name': 'foo', 'content_ml': 500, 'barcode': '123'},
        {'name': 'foo', 'content_ml': 500, 'price': 100},
        {'name': 'foo', 'content_ml': 500},
        {'name': 'foo', 'price': 100},
        {'name': 'foo', 'barcode': '123'},
        {'content_ml': 500, 'price': 100},
        {'content_ml': 500, 'barcode': '123'},
        {'price': 100, 'barcode': '123'},
        {'name': 'foo'},
        {'content_ml': 500},
        {'price': 100},
        {'barcode': '123'},
    )

    for data in datas:
        data['superuserpassword'] = config['DEFAULT']['superuser-password']
        req = requests.post('{}/drink/create'.format(API_URL), data=data)
        assert req.content == b'Incomplete request', 'input={}'.format(data)
        assert req.status_code == 400, 'input={}'.format(data)

def test_drink_creation_empty(flask_server):
    """Test if drink creation with empty string for parameter fails as expected."""
    import requests

    config = flask_server
    datas = (
        {'name': '', 'content_ml': 500, 'price': 100, 'barcode': '123'},
        {'name': 'foo', 'content_ml': 500, 'price': 100, 'barcode': ''},
    )

    for data in datas:
        data['superuserpassword'] = config['DEFAULT']['superuser-password']
        req = requests.post('{}/drink/create'.format(API_URL), data=data)
        assert req.content == b'Incomplete request', 'input={}'.format(data)
        assert req.status_code == 400, 'input={}'.format(data)

def test_drink_creation_superuser_wrong_pw(flask_server):
    """Test if drink creation with wrong superuser pw fails as expected."""
    import requests

    data = {
        'superuserpassword': '123',
        'name': 'foo',
        'content_ml': 500,
        'price': 100,
        'barcode': '123'
    }

    req = requests.post('{}/drink/create'.format(API_URL), data=data)
    assert req.content == b'Wrong superuserpassword'
    assert req.status_code == 400

def test_drink_view_good(flask_server, create_drink):
    """Test if drink view works."""
    import json
    import requests

    data = create_drink
    post_data = {'barcode': data['barcode']}

    req = requests.post('{}/drink/view'.format(API_URL), data=post_data)
    req.raise_for_status()
    assert json.loads(req.content.decode('utf-8')) == \
            [data['name'], data['content_ml'], data['price']]

def test_drink_view_inexistent_drink(flask_server, create_drink):
    """Test if drink view for inexistent drink fails as expected."""
    import requests

    data = create_drink
    data['barcode'] += '123'

    req = requests.post('{}/drink/view'.format(API_URL), data=data)
    assert req.content == b'No such drink in database'
    assert req.status_code == 400
