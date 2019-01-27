#!/usr/bin/env python3

import sqlite3
import json

from flask import Flask, g, request
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import BadRequestKeyError


DATABASE = './db.sqlite'
app = Flask(__name__)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
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
        user = query_db('SELECT password_hash FROM accounts WHERE name = ?',
                        [request.form['name']], one=True)
    except KeyError:
        return "Incomplete request", 400

    if user is None:
        return "No such user", 400

    if not check_password_hash(user['password_hash'],
                               request.form['password']):
        return "Wrong password", 400

@app.route('/api/account/create', methods=['POST'])
def account_create():
    """
    expects POST params:
    - name
    - password
    - barcode
    """
    try:
        password_hash = generate_password_hash(request.form['password'])
        query_db('INSERT INTO accounts (name, password_hash, barcode, saldo) VALUES (?, ?, ?, 0)',
                 [request.form['name'], password_hash, request.form['barcode']])
        get_db().commit()
    except BadRequestKeyError:
        return "Incomplete request", 400
    except sqlite3.IntegrityError:
        return "Database integrity error", 400
    except sqlite3.OperationalError as e:
        return e, 400
    return "ok"

@app.route('/api/account/modify', methods=['POST'])
def account_modify():
    """
    expects POST params:
    - name
    - password
    - new_name
    - new_password
    - barcode
    """
    ret = password_check(request)
    if ret:
        return ret

    try:
        new_password_hash = generate_password_hash(request.form['new_password'])
        test = query_db('UPDATE accounts SET name=?, password_hash=?, barcode=? WHERE name=?',
                        [request.form['new_name'], new_password_hash,
                         request.form['barcode'], request.form['name']])
        get_db().commit()
    except BadRequestKeyError:
        return "Incomplete request", 400
    except sqlite3.IntegrityError:
        return "Database integrity error", 400
    except sqlite3.OperationalError as e:
        return e, 400
    return "ok"

@app.route('/api/account/view', methods=['POST'])
def account_view():
    """
    expects POST params:
    - name
    - password
    """
    ret = password_check(request)
    if ret:
        return ret

    user = query_db('SELECT name, barcode, saldo FROM accounts WHERE name = ?',
                    [request.form['name']], one=True)

    return json.dumps(tuple(user))

@app.route('/api/money/add', methods=['POST'])
def money_add():
    """
    expects POST params:
    - name
    - password
    - money
    """
    ret = password_check(request)
    if ret:
        return ret

    user_id = query_db('SELECT id FROM accounts WHERE name=?',
                       [request.form['name']], one=True)
    user_id = tuple(user_id)[0]

    try:
        query_db('UPDATE accounts SET saldo=saldo+? WHERE id=?',
                 [request.form['money'], user_id])
        query_db('INSERT INTO money_logs (account_id, amount, timestamp) VALUES (?, ?, strftime("%s", "now"))',
                  [user_id, request.form['money']])
        get_db().commit()
    except BadRequestKeyError:
        return "Incomplete request", 400
    except sqlite3.IntegrityError:
        return "Databse integrity error", 400
    except sqlite3.OperationalError as e:
        return e, 400
    return "ok"

@app.route('/api/money/view', methods=['POST'])
def money_view():
    """
    expects POST params:
    - name
    - password
    """
    ret = password_check(request)
    if ret:
        return ret

    user_id = query_db('SELECT id FROM accounts WHERE name=?',
                       [request.form['name']], one=True)
    user_id = tuple(user_id)[0]
    try:
        transactions = query_db(
            'SELECT 0-drinks.price as amount, drinks.name as name, pay_logs.timestamp as timestamp FROM pay_logs INNER JOIN drinks ON pay_logs.drink_id=drinks.id WHERE pay_logs.account_id=? UNION SELECT amount, ? as drink_name, timestamp FROM money_logs WHERE account_id=?',
            [user_id, 'Guthaben aufgeladen', user_id]
        )
    except BadRequestKeyError:
        return "Incomplete request", 400
    except sqlite3.IntegrityError:
        return "Database integrity error", 400
    return json.dumps([tuple(row) for row in transactions])
