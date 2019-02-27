import subprocess
import os
import shutil
import signal
import tempfile
from datetime import datetime, timedelta
import re
import sqlite3
from configparser import ConfigParser

import pytest
import requests

START_TIMEOUT = 5
SAMPLE_CONFIG = './config.sample'
DB = './db.sqlite'
pytest.API_URL = 'http://127.0.0.1:5000/api'

def truncate_tables(db_fh, tables):
        db = sqlite3.connect(db_fh.name)
        for table in tables:
            cur = db.execute('DELETE FROM {}'.format(table))
            cur.close()
        db.commit()
        db.close()

def create_test_db():
    with open(DB, 'rb') as testdb:
        tmp_db = tempfile.NamedTemporaryFile()
        tmp_db.write(testdb.read())

        # order is important because of foreign keys
        truncate_tables(tmp_db, ('pay_logs', 'money_logs', 'accounts'))

        return tmp_db

def create_test_config(section, **options):
        sample_cfg = ConfigParser()
        sample_cfg.read(SAMPLE_CONFIG)

        for key, value in options.items():
            sample_cfg.set(section, key.replace('_', '-'), value)

        tmp_config = tempfile.NamedTemporaryFile(mode='wt')
        sample_cfg.write(tmp_config)
        tmp_config.seek(0)
        return tmp_config, sample_cfg

@pytest.fixture(scope='function')
def scanner_client():
    barcode_event = '/dev/input/event13'
    rfid_event = '/dev/input/event14'
    # FIXME: set callback using pytest.API_URL
    test_config, config = create_test_config(
        'scanner-client',
        scanner_device=barcode_event,
        rfid_device=rfid_event
    )
    env = os.environ.copy()
    env['CONFIG'] = test_config.name
    # run client
    cmd = 'umockdev-run -d {path}rfid.umockdev -i {barcode_event}={path}rfid.ioctl -e {barcode_event}={path}rfid.events -d {path}barcode.umockdev -i {rfid_event}={path}barcode.ioctl -e {rfid_event}={path}barcode.events -- python scanner-client.py' \
        .format(
            path='tests/umockdev/',
            barcode_event=barcode_event,
            rfid_event=rfid_event
        )
    proc = subprocess.Popen(cmd, shell=True, env=env,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            preexec_fn=os.setsid)

    # wait until client is running
    client_start = datetime.now()
    for line in iter(proc.stderr.readline, ''):
        if datetime.now() > client_start + timedelta(seconds=START_TIMEOUT):
            raise Exception('Client did not come up as expected')
        if line:
            print('client startup: ', line.decode('utf-8')[:-1])
        if line.strip().endswith(b'"0016027465" ordered "42254300"'):
            break

    yield config

    # kill client
    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    # print output for test debugging
    stdout, stderr = proc.communicate()
    for sout in stdout.decode('utf-8').split('\n'):
        print('stdout: {}'.format(sout))
    for serr in stderr.decode('utf-8').split('\n'):
        print('stderr: {}'.format(serr))

    # clean up tempfile by closing it
    test_config.close()

@pytest.fixture(scope='function')
def flask_server():
    test_db = create_test_db()
    test_config, config = create_test_config('DEFAULT', database=test_db.name)

    env = os.environ.copy()
    env['CONFIG'] = test_config.name
    env['FLASK_DEBUG'] = '1'

    # run server
    proc = subprocess.Popen('flask run --without-threads', shell=True, env=env,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            preexec_fn=os.setsid)

    # wait until server is running
    server_start = datetime.now()
    for line in iter(proc.stderr.readline, ''):
        if datetime.now() > server_start + timedelta(seconds=START_TIMEOUT):
            raise Exception('Server did not come up as expected')
        if line:
            print('server startup: ', line.decode('utf-8')[:-1])
        if line.startswith(b' * Running on'):
            break

    yield config

    # kill server
    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    # print output for test debugging
    stdout, stderr = proc.communicate()
    for sout in stdout.decode('utf-8').split('\n'):
        print('stdout: {}'.format(sout))
    for serr in stderr.decode('utf-8').split('\n'):
        print('stderr: {}'.format(serr))

    # clean up tempfiles by closing them
    test_db.close()
    test_config.close()

@pytest.fixture(scope='function')
def create_account():
    data = {'name': 'foo', 'password':'bar', 'barcode': '123'}
    requests.post('{}/account/create'.format(pytest.API_URL), data=data)
    return data

@pytest.fixture(scope='function')
def create_account_with_1_euro(create_account):
    data = create_account
    data['money'] = 100
    requests.post('{}/money/add'.format(pytest.API_URL), data=data)
    return data
