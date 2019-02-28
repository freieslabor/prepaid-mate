import pytest
import re
import subprocess

def test_client(flask_server, create_account_with_balance, scanner_client):
    create_account_with_balance(150)
    proc = scanner_client()

    def get_log_line(logger='.*:root:'):
        for line in iter(proc.stderr.readline, ''):
            line = line.decode('utf-8')
            if re.search(logger, line):
                return line

    assert 'account barcode: 0016027465' in get_log_line()
    assert 'account "0016027465" ordered "42254300"'  in get_log_line()
    assert 'calling {}'.format(pytest.API_URL) in get_log_line()
    assert 'callback successful: ' in get_log_line()
