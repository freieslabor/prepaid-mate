"""Test scanner_client.py with flask server."""
# disable unused arguments used to run fixtures
# pylint: disable=unused-argument

import re

import pytest

API_URL = pytest.API_URL  # pylint: disable=no-member

def test_client(flask_server, create_account_with_balance, scanner_client):
    """Test payment on scanner_client.py with flask server and preset account."""
    create_account_with_balance(150)
    proc = scanner_client()

    def get_log_line(logger='.*:root:'):
        for line in iter(proc.stderr.readline, ''):
            line = line.decode('utf-8')
            if re.search(logger, line):
                return line

        return None

    assert 'account code: 0016027465' in get_log_line()
    assert 'account "0016027465" ordered "42254300"'  in get_log_line()
    assert 'calling {}'.format(API_URL) in get_log_line()
    assert 'callback successful: ' in get_log_line()
