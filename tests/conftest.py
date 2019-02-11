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

START_TIMEOUT = 5
SAMPLE_CONFIG = './config.sample'
DB = './db.sqlite'

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

def create_test_config(test_db):
        sample_cfg = ConfigParser()
        sample_cfg.read(SAMPLE_CONFIG)
        sample_cfg.set('DEFAULT', 'database', test_db.name)

        tmp_config = tempfile.NamedTemporaryFile(mode='wt')
        sample_cfg.write(tmp_config)
        tmp_config.seek(0)
        return tmp_config

@pytest.fixture(scope='function')
def flask_server():
    test_db = create_test_db()
    test_config = create_test_config(test_db)

    env = os.environ.copy()
    env["CONFIG"] = test_config.name

    # run server
    proc = subprocess.Popen('flask run --without-threads', shell=True, env=env,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            preexec_fn=os.setsid)

    # wait until server is running
    server_start = datetime.now()
    for line in iter(proc.stderr.readline, ""):
        if datetime.now() > server_start + timedelta(seconds=START_TIMEOUT):
            raise Exception('Server did not come up as expected')
        if line:
            print("server startup: ", line.decode('utf-8')[:-1])
        if line.startswith(b' * Running on'):
            break

    yield test_config

    # kill server
    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    # print output for test debugging
    stdout, stderr = proc.communicate()
    print(stdout.decode('utf-8'))
    print(stderr.decode('utf-8'))

    # clean up tempfiles by closing them
    test_db.close()
    test_config.close()
