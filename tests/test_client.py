"""Test scanner_client.py with flask server."""
# disable unused arguments used to run fixtures
# pylint: disable=unused-argument

import pytest

def test_client(flask_server, create_account_with_balance, scanner_client):
    """Test payment on scanner_client.py with flask server and preset account."""
    import re

    create_account_with_balance(150)
    proc = scanner_client()

    def get_log_line(logger='.*:root:'):
        for line in iter(proc.stderr.readline, ''):
            line = line.decode('utf-8')
            if re.search(logger, line):
                return line

        return None

    assert 'account code: 0016027465' in get_log_line()
    get_log_line() # ignore user greeting
    assert 'account "0016027465" ordered "42254300"'  in get_log_line()
    assert 'calling API with' in get_log_line()
    assert 'callback successful: ' in get_log_line()
