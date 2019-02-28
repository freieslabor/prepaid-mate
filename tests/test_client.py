import pytest

def test_client(flask_server, scanner_client):
    _, proc = scanner_client

    assert 'account barcode: 0016027465' in proc.stderr.readline().decode('utf-8')
    assert 'account "0016027465" ordered "42254300"'  in proc.stderr.readline().decode('utf-8')
    assert 'calling {}'.format(pytest.API_URL) in proc.stderr.readline().decode('utf-8')
    #assert 'callback successfull: ' in proc.stderr.readline().decode('utf-8')
