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
    user = query_db('SELECT * FROM accounts WHERE name = ?',
       [request.form['name']], one=True)

    if user is None:
        return "no such user", 400

    if not check_password_hash(user['password_hash'],
                               request.form['password']):
        return "wrong pw", 400

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
        return "Integrity error", 400
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
        return "Integrity error", 400
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

    try:
        test = query_db('UPDATE accounts SET saldo=saldo+? WHERE name=?',
                 [request.form['money'], request.form['name']])
        get_db().commit()
    except BadRequestKeyError:
        return "Incomplete request", 400
    except sqlite3.IntegrityError:
        return "Integrity error", 400
    return "ok"
