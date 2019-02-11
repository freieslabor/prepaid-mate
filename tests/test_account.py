import requests

def test_account_creation(flask_server):
    r = requests.post('http://127.0.0.1:5000/api/account/create',
                      data={'name': 'foo', 'password':'bar', 'barcode': '123'})
    assert r.status_code == 200
    assert r.content == b'ok'
