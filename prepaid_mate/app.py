#!/usr/bin/env python3
"""Flask Prepaid Mate server"""

import os
import sqlite3
import json
from configparser import ConfigParser
import tempfile
import time

from flask import Flask, g, request
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import BadRequestKeyError

app = Flask(__name__)  # pylint: disable=invalid-name
CONF = ConfigParser()
CONF_FILE = os.environ.get('CONFIG', './config')
CONF.read_file(open(CONF_FILE))
UNKNOWN_CODE = tempfile.NamedTemporaryFile()

def sql_integrity_error(exc):
    """Extract useful info from """
    assert isinstance(exc, sqlite3.IntegrityError)

    unique_error_prefix = 'UNIQUE constraint failed: '
    if exc.args[0].startswith(unique_error_prefix):
        field = exc.args[0].replace(unique_error_prefix, '')
        _, field = field.split('.', 1)
        return '{} already exists'.format(field), 400
    return 'Database integrity error', 400

def get_db():
    """
    Helper to retrieve DB connection, taken from
    http://flask.pocoo.org/docs/1.0/patterns/sqlite3/
    """
    database = getattr(g, '_database', None)
    if database is None:
        database = g._database = sqlite3.connect(CONF.get('DEFAULT', 'database'))
    database.row_factory = sqlite3.Row
    return database

@app.teardown_appcontext
def close_connection(_):
    """
    Helper to retrieve DB connection
    http://flask.pocoo.org/docs/1.0/patterns/sqlite3/
    """
    database = getattr(g, '_database', None)
    if database is not None:
        database.close()

def query_db(query, args=(), one=False):
    """
    Helper to query DB
    http://flask.pocoo.org/docs/1.0/patterns/sqlite3/
    """
    cur = get_db().execute(query, args)
    result = cur.fetchall()
    cur.close()
    return (result[0] if result else None) if one else result

def password_check(req):
    """
    Helper to check username and password, taken from "name" and "password"
    POST parameters.
    """
    try:
        account = query_db('SELECT id, password_hash FROM accounts WHERE name = ?',
                           [req.form['name']], one=True)
        if 'password' not in req.form:
            app.logger.info('password check failed: no password given')
            raise KeyError()
    except KeyError:
        app.logger.info('password check failed: no username given')
        raise KeyError('Incomplete request')

    try:
        account_id, password_hash = tuple(account)
    except TypeError:
        app.logger.info('password check failed: no such account "%s" in database',
                 req.form['name'])
        raise TypeError('No such account in database')

    if not check_password_hash(password_hash, req.form['password']):
        app.logger.info('password check failed: wrong password for account "%s"',
                 req.form['name'])
        raise ValueError('Wrong password')

    return account_id

@app.route('/api/account/create', methods=['POST'])
def account_create():
    """
    Creates account with given parameters.

    Expects POST parameters:
    - name
    - password
    - code

    Returns:
    200 "ok"
    400 with error message
    500 on broken code
    """
    try:
        drink_barcode = query_db('SELECT barcode FROM drinks WHERE barcode= ?',
                                 [request.form['code']], one=True)
        if drink_barcode is not None:
            return 'This code is already used for a drink', 400

        password_hash = generate_password_hash(request.form['password'])
        query_db('INSERT INTO accounts (name, password_hash, barcode, saldo) VALUES (?, ?, ?, 0)',
                 [request.form['name'], password_hash, request.form['code']])

        if request.form['name'] == '' or request.form['password'] == '' \
            or request.form['code'] == '':
            get_db().rollback()
            raise BadRequestKeyError

        get_db().commit()
        app.logger.info('Account "%s (identifier: "%s") created',
                 request.form['name'], request.form['code'])
    except BadRequestKeyError:
        exc_str = 'Incomplete request'
        app.logger.warning(exc_str)
        return exc_str, 400
    except sqlite3.IntegrityError as exc:
        exc_str = sql_integrity_error(exc)
        app.logger.error(exc_str)
        return exc_str
    except sqlite3.OperationalError as exc:
        app.logger.error(exc)
        return exc, 400

    return 'ok'

@app.route('/api/account/modify', methods=['POST'])
def account_modify():
    """
    Modifies account identified by "name" and "password" with given parameters.

    Expects POST parameters:
    - name
    - password
    - new_name
    - new_password
    - new_code

    Returns 200 "ok"
    400 with error message
    500 on broken code
    """
    try:
        password_check(request)
    except (KeyError, TypeError, ValueError) as exc:
        return exc.args[0], 400

    try:
        new_password_hash = generate_password_hash(request.form['new_password'])
        query_db('UPDATE accounts SET name=?, password_hash=?, barcode=? WHERE name=?',
                 [request.form['new_name'], new_password_hash,
                  request.form['new_code'], request.form['name']])

        if request.form['new_name'] == '' or request.form['new_password'] == '' \
            or request.form['new_code'] == '':
            get_db().rollback()
            raise BadRequestKeyError

        get_db().commit()
        app.logger.info('Account "%s modified', request.form['name'])
    except BadRequestKeyError:
        exc_str = 'Incomplete request'
        app.logger.warning(exc_str)
        return exc_str, 400
    except sqlite3.IntegrityError as exc:
        exc_str = sql_integrity_error(exc)
        app.logger.error(exc_str)
        return exc_str, 400
    except sqlite3.OperationalError as exc:
        app.logger.error(exc)
        return exc, 400

    return 'ok'

@app.route('/api/account/view', methods=['POST'])
def account_view():
    """
    Returns information on account identified by "name" and "password".

    Expects POST parameters:
    - name
    - password

    Returns 200 with json tuple (name, barcode, saldo)
    400 with error message
    500 on broken code
    """
    try:
        password_check(request)
    except (KeyError, TypeError, ValueError) as exc:
        return exc.args[0], 400

    account = query_db('SELECT name, barcode, saldo FROM accounts WHERE name = ?',
                       [request.form['name']], one=True)

    return json.dumps(tuple(account))

@app.route('/api/account/code_exists', methods=['POST'])
def account_exists():
    """
    Returns true and account name if the given account identified by code exists
    otherwise false and null. If the account does not exist the code is saved
    in a temporary file as a side-effect.

    Expects POST parameters:
    - code

    Returns 200 with json tuple (bool, account_name)
    400 with error message
    500 on broken code
    """

    try:
        account_name = query_db('SELECT name FROM accounts WHERE barcode = ?',
                                [request.form['code']], one=True)
        if account_name is None:
            UNKNOWN_CODE.write(request.form['code'].encode('utf-8'))
            UNKNOWN_CODE.seek(0)
        else:
            account_name = tuple(account_name)[0]

        return json.dumps((account_name is not None, account_name))
    except KeyError:
        return 'Incomplete request', 400
    except sqlite3.IntegrityError as exc:
        exc_str = sql_integrity_error(exc)
        app.logger.error(exc_str)
        return exc_str, 400
    except sqlite3.OperationalError as exc:
        app.logger.error(exc)
        return exc, 400

@app.route('/api/money/add', methods=['POST'])
def money_add():
    """
    Add "money" to account identified "name" and "password".

    Expects POST parameters:
    - name
    - password
    - money

    Returns 200 "ok"
    400 with error message
    500 on broken code
    """
    try:
        account_id = password_check(request)
    except (KeyError, TypeError, ValueError) as exc:
        return exc.args[0], 400

    try:
        try:
            money = int(request.form['money'])
        except ValueError:
            app.logger.info('Money for "%s" not given in cents', request.form['name'])
            return 'Money must be specified in cents', 400

        account_saldo = query_db('SELECT saldo FROM accounts WHERE id = ?',
                                 [account_id], one=True)
        account_saldo = tuple(account_saldo)[0]

        if account_saldo + money < 0:
            app.logger.info('Negative amount would lead to negative balance')
            return 'Negative amount would lead to negative balance', 400

        query_db('UPDATE accounts SET saldo=saldo+? WHERE id=?',
                 [money, account_id])
        query_db('INSERT INTO money_logs (account_id, amount, timestamp) VALUES (?, ?, strftime("%s", "now"))',  # pylint: disable=line-too-long
                 [account_id, money])
        get_db().commit()
        app.logger.info('Added %d cents to account "%s"', money, request.form['name'])
    except Exception as exc:  # pylint: disable=broad-except
        get_db().rollback()
        if isinstance(exc, (BadRequestKeyError, KeyError)):
            exc_str = 'Incomplete request'
        elif isinstance(exc, sqlite3.IntegrityError):
            exc_str = sql_integrity_error(exc)
        else:
            exc_str = str(exc)

        app.logger.error(exc_str)
        return exc_str, 400

    return 'ok'

@app.route('/api/money/view', methods=['POST'])
def money_view():
    """
    View transactions of account identified "name" and "password".

    Expects POST parameters:
    - name
    - password

    Returns 200 with json tuple (amount, transaction name, timestamp, drink
                                 barcode if available)
    400 with error message
    500 on broken code
    """
    try:
        account_id = password_check(request)
    except (KeyError, TypeError, ValueError) as exc:
        return exc.args[0], 400

    try:
        transactions = query_db(
            'SELECT 0-drinks.price as amount, drinks.name as name, pay_logs.timestamp as timestamp, drinks.barcode as barcode FROM pay_logs INNER JOIN drinks ON pay_logs.drink_id=drinks.id WHERE pay_logs.account_id=? UNION SELECT amount, ? as drink_name, timestamp, "" as drinks_barcode FROM money_logs WHERE account_id=? ORDER BY timestamp DESC',  # pylint: disable=line-too-long
            [account_id, 'Guthaben aufgeladen', account_id]
        )
    except BadRequestKeyError:
        exc_str = 'Incomplete request'
        app.logger.warning(exc_str)
        return exc_str, 400
    except sqlite3.IntegrityError as exc:
        exc_str = sql_integrity_error(exc)
        app.logger.error(exc_str)
        return exc_str, 400

    return json.dumps([tuple(row) for row in transactions])

@app.route('/api/payment/perform', methods=['POST'])
def payment_perform():
    """
    Perform payment transaction ("drink_barcode") on account identified by
    "account_code". This is authorized on "superuserpassword".

    Expects POST parameters:
    - superuserpassword
    - account_code
    - drink_barcode

    Returns 200 with json tuple (amount, transaction name, timestamp)
    400 with error message
    500 on broken code
    """
    if request.form['superuserpassword'] != \
        CONF.get('DEFAULT', 'superuser-password'):
        app.logger.warning('Payment with wrong super user password')
        return 'Wrong superuserpassword', 400

    try:
        account = query_db('SELECT id, saldo FROM accounts WHERE barcode=?',
                           [request.form['account_code']], one=True)
        try:
            account_id, saldo = tuple(account)
        except TypeError:
            exc_str = 'Barcode does not belong to an account'
            app.logger.warning(exc_str)
            return exc_str, 400

        if account_id is None:
            exc_str = 'No such account in database'
            app.logger.warning(exc_str)
            return exc_str, 400

        drink = query_db('SELECT id, price FROM drinks WHERE barcode=?',
                         [request.form['drink_barcode']], one=True)
        try:
            drink_id, drink_price = tuple(drink)
        except TypeError:
            exc_str = 'No such drink in database'
            app.logger.warning(exc_str)
            return exc_str, 400

        if saldo - drink_price < 0:
            exc_str = 'Insufficient funds'
            app.logger.warning(exc_str)
            return exc_str, 400

        query_db('INSERT INTO pay_logs (account_id, drink_id, timestamp) VALUES (?, ?, strftime("%s", "now"))',  # pylint: disable=line-too-long
                 [account_id, drink_id])
        query_db('UPDATE accounts SET saldo=saldo-? WHERE id=?',
                 [drink_price, account_id])
        get_db().commit()
        app.logger.warning('Account ID "%s" ordered %s (%d cents), new saldo=%d cents',
                    account_id, drink_id, drink_price, saldo)
        return str(saldo - drink_price)
    except Exception as exc:  # pylint: disable=broad-except
        get_db().rollback()
        if isinstance(exc, BadRequestKeyError):
            exc_str = 'Incomplete request'
        elif isinstance(exc, sqlite3.IntegrityError):
            exc_str = sql_integrity_error(exc)
        else:
            exc_str = str(exc)

        app.logger.warning(exc_str)
        return exc_str, 400

@app.route('/api/last_unknown_code', methods=['GET'])
def last_unknown_code():
    """
    Returns last unknown code seen in the last 60 seconds or empty string.

    Returns 200 with last known code as string or empty string
    500 on broken code
    """
    code = ''

    if time.time() < os.stat(UNKNOWN_CODE.name).st_mtime + 60:
        code = UNKNOWN_CODE.read().decode('utf-8')
        UNKNOWN_CODE.seek(0)

    return code


if __name__ == "__main__":
    app.run(host='127.0.0.1')
