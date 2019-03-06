"""pytest fixtures and helpers"""
import pytest

START_TIMEOUT = 5
SAMPLE_CONFIG = './config.sample'
DB = './db.sqlite'
pytest.API_URL = 'http://localhost:5000/api'

def truncate_tables(db_fh, tables):
    """Truncate the tables given"""
    import sqlite3

    database = sqlite3.connect(db_fh.name)
    for table in tables:
        cur = database.execute('DELETE FROM {}'.format(table))
        cur.close()
    database.commit()
    database.close()

def create_test_db():
    """
    Uses db.sqlite, generates temporary copy and truncates all tables but drinks
    """
    import tempfile

    with open(DB, 'rb') as testdb:
        tmp_db = tempfile.NamedTemporaryFile()
        tmp_db.write(testdb.read())

        # order is important because of foreign keys
        truncate_tables(tmp_db, ('pay_logs', 'money_logs', 'accounts'))

        return tmp_db

def create_test_config(section, **options):
    """
    Uses config.sample, generates temporary copy and sets given options.
    Underscores in keys from kwargs are replaced with minuses.
    """
    from configparser import ConfigParser
    import tempfile

    sample_cfg = ConfigParser()
    sample_cfg.read(SAMPLE_CONFIG)

    for key, value in options.items():
        sample_cfg.set(section, key.replace('_', '-'), value)

    tmp_config = tempfile.NamedTemporaryFile(mode='wt')
    sample_cfg.write(tmp_config)
    tmp_config.seek(0)
    return tmp_config, sample_cfg

def start_process_operational(cmd, cfg, operational_re, cmd_name, env=None):
    """
    Start "cmd" as subprocess with given "cfg" and "env". It is supervised
    until operational_re matches. "cmd_name" is used to name the logger.
    """
    import subprocess
    import logging
    import os
    import signal
    import re

    logger = logging.getLogger(cmd_name)

    if env is None:
        env = os.environ.copy()
    env['CONFIG'] = cfg.name

    # run process
    try:
        proc = subprocess.Popen(cmd, shell=True, env=env,   # pylint: disable=subprocess-popen-preexec-fn
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                preexec_fn=os.setsid)

        # wait until process reached operational state
        for line in iter(proc.stderr.readline, ''):
            line_dec = line.decode('utf-8')
            logger.info(line_dec.strip())
            if re.search(operational_re, line_dec):
                break
    except KeyboardInterrupt:
        # make sure all subprocess are killed first
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        raise

    return proc

def end_process(proc, cmd_name):
    """
    End a process started with start_process_operational(). Log stdout/stderr
    with logger with name "cmd_name" emitted by the process.
    """
    import logging
    import os
    import signal

    logger = logging.getLogger(cmd_name)
    # kill process group
    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    # log output for test debugging
    stdout, stderr = proc.communicate()
    for sout in stdout.decode('utf-8').split('\n'):
        if sout.strip():
            logger.info(sout)

    for serr in stderr.decode('utf-8').split('\n'):
        if serr.strip():
            logger.warning(serr)

@pytest.fixture(scope='function')
def scanner_client(caplog):
    """Start scanner_client.py and emulate RFID and barcode scanner."""
    import logging

    procs = []
    configs = []
    names = []
    def _scanner_client(enabled=('rfid', 'barcode')):
        # decrease log level to be able to debug scanner client
        caplog.set_level(logging.INFO)
        names.append('scanner client')

        event_devices = {
            'rfid_device': '/dev/input/event14',
            'barcode_device': '/dev/input/event13'
        }

        if isinstance(enabled, str):
            enabled = [enabled]

        configs.append(create_test_config('scanner-client', **event_devices)[0])
        # run client
        cmd = 'umockdev-run'
        for name, dev in event_devices.items():
            name = name.replace('_device', '')
            cmd += ' -d {path}{name}.umockdev -i {dev}={path}{name}.ioctl' \
                .format(path='tests/umockdev/', name=name, dev=dev)

            if name in enabled:
                cmd += ' -e {dev}={path}{name}.events' \
                    .format(path='tests/umockdev/', name=name, dev=dev)

        cmd += ' -- python scanner_client.py'
        procs.append(start_process_operational(cmd, configs[-1], 'Prepaid Mate up and running',
                                               names[-1]))

        return procs[-1]

    yield _scanner_client

    # clean up
    for proc, config, name in zip(procs, configs, names):
        end_process(proc, name)

        # clean up tempfile by closing it
        config.close()

@pytest.fixture(scope='function')
def flask_server(caplog, pytestconfig):
    """Start flask server."""
    import logging
    import os

    # decrease log level to be able to debug flask server
    caplog.set_level(logging.INFO)
    name = 'flask server'
    test_db = create_test_db()
    test_config, config = create_test_config('DEFAULT', database=test_db.name)

    env = os.environ.copy()
    if pytestconfig.getoption("verbose"):
        env['FLASK_DEBUG'] = '1'

    proc = start_process_operational('flask run --without-threads --no-reload', test_config,
                                     r' \* Running on', name, env=env)

    yield config

    end_process(proc, name)

    # clean up tempfiles by closing them
    test_db.close()
    test_config.close()

@pytest.fixture(scope='function')
def create_account():
    """Create an account with some predefined parameters."""
    import requests

    # the identifier matches the rfid code in tests/umockdev/rfid.events
    data = {'name': 'foo', 'password':'bar', 'code': '0016027465'}
    requests.post('{}/account/create'.format(pytest.API_URL), data=data)
    return data

@pytest.fixture(scope='function')
def create_account_with_balance(create_account):  # pylint: disable=redefined-outer-name
    """
    Create an account with some predefined parameters with a balance given.
    """
    import requests

    data = create_account

    def _create_account_with_balance(balance):
        data['money'] = balance
        requests.post('{}/money/add'.format(pytest.API_URL), data=data)
        return data

    return _create_account_with_balance
