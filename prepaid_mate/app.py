#!/usr/bin/env python3
"""Flask Prepaid Mate server"""

import logging
import os
import sqlite3
import json
import tempfile
import time

from flask import Flask, g, request
from werkzeug.security import generate_password_hash
from werkzeug.exceptions import BadRequestKeyError

from .app_helper import (sql_integrity_error, get_db, query_db, password_check,
                         superuser_password_check)

app = Flask(__name__)  # pylint: disable=invalid-name
UNKNOWN_CODE = tempfile.NamedTemporaryFile()

@app.teardown_appcontext
def close_connection(_):
    """
    Helper to retrieve DB connection
    http://flask.pocoo.org/docs/1.0/patterns/sqlite3/
    """
    database = getattr(g, '_database', None)
    if database is not None:
        database.close()

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
        code = request.form['code']
        password = request.form['password']
        name = request.form['name']

        drink_barcode = query_db('SELECT barcode FROM drinks WHERE barcode=?', [code], one=True)
        if drink_barcode is not None:
            return 'This code is already used for a drink', 400

        password_hash = generate_password_hash(password)
        query_db('INSERT INTO accounts (name, password_hash, barcode, saldo) VALUES (?, ?, ?, 0)',
                 [name, password_hash, code])

        if not all((name, password, code)):
            get_db().rollback()
            raise BadRequestKeyError

        get_db().commit()
        app.logger.info('Account "%s (identifier: "%s") created', name, code)
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
    - new_name (optional)
    - new_password (optional)
    - new_code (optional)

    Alternative POST parameters:
    - superuserpassword
    - name
    - new_name (optional)
    - new_password (optional)
    - new_code (optional)

    Returns 200 "ok"
    400 with error message
    500 on broken code
    """
    try:
        password_check(app, request)
    except (KeyError, TypeError, ValueError) as exc:
        return exc.args[0], 400

    name = request.form['name']

    try:
        try:
            new_code = request.form['new_code']
            if not new_code:
                raise ValueError
            query_db('UPDATE accounts SET barcode=? WHERE name=?', [new_code, name])
        except BadRequestKeyError:
            # optional parameter
            pass

        try:
            new_password = request.form['new_password']
            if not new_password:
                raise ValueError
            new_password_hash = generate_password_hash(request.form['new_password'])
            query_db('UPDATE accounts SET password_hash=? WHERE name=?',
                     [new_password_hash, name])
        except BadRequestKeyError:
            # optional parameter
            pass

        try:
            new_name = request.form['new_name']
            if not new_name:
                raise ValueError
            query_db('UPDATE accounts SET name=? WHERE name=?',
                     [new_name, name])
        except BadRequestKeyError:
            pass

        get_db().commit()
        app.logger.info('Account "%s modified (name=%d, code=%d, password=%d)',
                            request.form['name'], 'new_name' in request.form,
                            'new_code' in request.form, 'new_password' in request.form)

    except Exception as exc:
        get_db().rollback()
        if isinstance(exc, ValueError):
            exc_str = 'Incomplete request'
        elif isinstance(exc, sqlite3.IntegrityError):
            exc_str = sql_integrity_error(exc)
        elif isinstance(exc, sqlite3.OperationalError):
            exc_str = exc.args[0]

        app.logger.error(exc_str)
        return exc_str, 400

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
        account_id, _ = password_check(app, request)

        account = query_db('SELECT name, barcode, saldo FROM accounts WHERE id=?',
                           [account_id], one=True)
    except (KeyError, TypeError, ValueError) as exc:
        return exc.args[0], 400

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
        code = request.form['code']
        account_name = query_db('SELECT name FROM accounts WHERE barcode = ?',
                                [code], one=True)
        if account_name is None:
            UNKNOWN_CODE.truncate(0)
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

    Alternative POST parameters:
    - superuserpassword
    - account_code
    - money

    Returns 200 "ok"
    400 with error message
    500 on broken code
    """
    try:
        account_id, name = password_check(app, request)
    except (KeyError, TypeError, ValueError) as exc:
        return exc.args[0], 400

    try:
        try:
            money = int(request.form['money'])
        except ValueError:
            app.logger.info('Money for "%s" not given in cents', name)
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
        app.logger.info('Added %d cents to account "%s"', money, name)

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
        account_id, _ = password_check(app, request)
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
    "account_code". This is authorized with "superuserpassword".

    Expects POST parameters:
    - superuserpassword
    - account_code
    - drink_barcode

    Returns 200 with json tuple (amount, transaction name, timestamp)
    400 with error message
    500 on broken code
    """
    try:
        superuser_password_check(app, request)
    except (KeyError, TypeError, ValueError) as exc:
        return exc.args[0], 400

    try:
        account_code = request.form['account_code']
        drink_barcode = request.form['drink_barcode']

        account = query_db('SELECT id, saldo FROM accounts WHERE barcode=?',
                           [account_code], one=True)
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

        drink = query_db('SELECT id, price FROM drinks WHERE barcode=?', [drink_barcode], one=True)
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
else:
    GUNICORN_LOGGER = logging.getLogger('gunicorn.error')
    app.logger.handlers = GUNICORN_LOGGER.handlers
    app.logger.setLevel(GUNICORN_LOGGER.level)
