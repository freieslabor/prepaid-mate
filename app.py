#!/usr/bin/env python3

import os
import sqlite3
import json

from flask import Flask, g, request
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import BadRequestKeyError
from configparser import ConfigParser

conf = ConfigParser()
conf_file = os.environ.get('CONFIG', './config')
conf.read_file(open(conf_file))
app = Flask(__name__)

def sql_integrity_error(e):
    unique_error_prefix = 'UNIQUE constraint failed: '
    if e.args[0].startswith(unique_error_prefix):
        field = e.args[0].replace(unique_error_prefix, '')
        _, field = field.split('.', 1)
        return '{} already exists'.format(field), 400
    return 'Database integrity error', 400

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(conf.get('DEFAULT', 'database'))
    db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def password_check(request):
    try:
        account = query_db('SELECT id, password_hash FROM accounts WHERE name = ?',
                        [request.form['name']], one=True)
        if 'password' not in request.form:
            raise KeyError
    except KeyError:
        raise Exception('Incomplete request')

    try:
        account_id, password_hash = tuple(account)
    except TypeError:
        raise Exception('No such account in database')

    if not check_password_hash(password_hash, request.form['password']):
        raise Exception('Wrong password')

    return account_id

@app.route('/api/account/create', methods=['POST'])
def account_create():
    """
    expects POST params:
    - name
    - password
    - barcode
    """

    try:
        drink_barcode = query_db('SELECT barcode FROM drinks WHERE barcode= ?',
                                  [request.form['barcode']], one=True)
        if drink_barcode is not None:
            return 'This barcode is already used for a drink', 400

        password_hash = generate_password_hash(request.form['password'])
        query_db('INSERT INTO accounts (name, password_hash, barcode, saldo) VALUES (?, ?, ?, 0)',
                 [request.form['name'], password_hash, request.form['barcode']])

        if request.form['name'] == '' or request.form['password'] == '' \
            or request.form['barcode'] == '':
            get_db().rollback()
            raise BadRequestKeyError

        get_db().commit()
    except BadRequestKeyError:
        return 'Incomplete request', 400
    except sqlite3.IntegrityError as e:
        return sql_integrity_error(e)
    except sqlite3.OperationalError as e:
        return e, 400

    return 'ok'

@app.route('/api/account/modify', methods=['POST'])
def account_modify():
    """
    expects POST params:
    - name
    - password
    - new_name
    - new_password
    - new_barcode
    """
    try:
        password_check(request)
    except Exception as e:
        return e.args[0], 400

    try:
        new_password_hash = generate_password_hash(request.form['new_password'])
        test = query_db('UPDATE accounts SET name=?, password_hash=?, barcode=? WHERE name=?',
                        [request.form['new_name'], new_password_hash,
                         request.form['new_barcode'], request.form['name']])

        if request.form['new_name'] == '' or request.form['new_password'] == '' \
            or request.form['new_barcode'] == '':
            get_db().rollback()
            raise BadRequestKeyError

        get_db().commit()
    except BadRequestKeyError:
        return 'Incomplete request', 400
    except sqlite3.IntegrityError:
        return 'Database integrity error', 400
    except sqlite3.OperationalError as e:
        return e, 400

    return 'ok'

@app.route('/api/account/view', methods=['POST'])
def account_view():
    """
    expects POST params:
    - name
    - password
    """
    try:
        password_check(request)
    except Exception as e:
        return e.args[0], 400

    account = query_db('SELECT name, barcode, saldo FROM accounts WHERE name = ?',
                    [request.form['name']], one=True)

    return json.dumps(tuple(account))

@app.route('/api/money/add', methods=['POST'])
def money_add():
    """
    expects POST params:
    - name
    - password
    - money
    """
    try:
        account_id = password_check(request)
    except Exception as e:
        return e.args[0], 400

    try:
        try:
            money = int(request.form['money'])
        except ValueError:
            return 'Money must be specified in cents', 400

        if money <= 0:
            return 'Zero/negative money given', 400

        query_db('UPDATE accounts SET saldo=saldo+? WHERE id=?',
                 [money, account_id])
        query_db('INSERT INTO money_logs (account_id, amount, timestamp) VALUES (?, ?, strftime("%s", "now"))',
                  [account_id, money])
        get_db().commit()
    except Exception as e:
        get_db().rollback()
        if isinstance(e, (BadRequestKeyError, KeyError)):
            return 'Incomplete request', 400
        if isinstance(e, sqlite3.IntegrityError):
            return 'Database integrity error', 400
        if isinstance(e, sqlite3.OperationalError):
            return e, 400

    return 'ok'

@app.route('/api/money/view', methods=['POST'])
def money_view():
    """
    expects POST params:
    - name
    - password
    """
    try:
        account_id = password_check(request)
    except Exception as e:
        return e.args[0], 400

    try:
        transactions = query_db(
            'SELECT 0-drinks.price as amount, drinks.name as name, pay_logs.timestamp as timestamp FROM pay_logs INNER JOIN drinks ON pay_logs.drink_id=drinks.id WHERE pay_logs.account_id=? UNION SELECT amount, ? as drink_name, timestamp FROM money_logs WHERE account_id=? ORDER BY timestamp DESC',
            [account_id, 'Guthaben aufgeladen', account_id]
        )
    except BadRequestKeyError:
        return 'Incomplete request', 400
    except sqlite3.IntegrityError:
        return 'Database integrity error', 400

    return json.dumps([tuple(row) for row in transactions])

@app.route('/api/payment/perform', methods=['POST'])
def payment_perform():
    """
    expects POST params:
    - superuserpassword
    - account_barcode
    - drink_barcode
    """
    if request.form['superuserpassword'] != \
        conf.get('DEFAULT', 'superuser-password'):
        return 'Wrong superuserpassword', 400

    try:
        account = query_db('SELECT id, saldo FROM accounts WHERE barcode=?',
                       [request.form['account_barcode']], one=True)
        try:
            account_id, saldo = tuple(account)
        except TypeError:
            return 'Barcode does not belong to an account', 400

        if account_id is None:
            return 'No such account in database', 400

        drink = query_db('SELECT id, price FROM drinks WHERE barcode=?',
                       [request.form['drink_barcode']], one=True)
        print("drink_barcode = " + request.form['drink_barcode'])
        try:
            drink_id, drink_price = tuple(drink)
        except TypeError:
            return 'No such drink in database', 400

        if saldo - drink_price < 0:
            return 'Insufficient funds', 400

        query_db('INSERT INTO pay_logs (account_id, drink_id, timestamp) VALUES (?, ?, strftime("%s", "now"))',
                 [account_id, drink_id])
        query_db('UPDATE accounts SET saldo=saldo-? WHERE id=?',
                 [drink_price, account_id])
        get_db().commit()
    except Exception as e:
        get_db().rollback()
        if isinstance(e, BadRequestKeyError):
            return 'Incomplete request', 400
        if isinstance(e, sqlite3.IntegrityError):
            return 'Database integrity error', 400

    return 'ok'
