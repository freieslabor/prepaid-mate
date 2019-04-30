#!/usr/bin/env python3
"""Flask Prepaid Mate server helper"""

import os
import sqlite3
from configparser import ConfigParser

from flask import g
from werkzeug.security import check_password_hash
from werkzeug.exceptions import BadRequestKeyError

CONF = ConfigParser()
CONF_FILE = os.environ.get('CONFIG', './config')
CONF.read_file(open(CONF_FILE))

def sql_integrity_error(exc):
    """Extract useful info from """
    assert isinstance(exc, sqlite3.IntegrityError)

    unique_error_prefix = 'UNIQUE constraint failed: '
    if exc.args[0].startswith(unique_error_prefix):
        field = exc.args[0].replace(unique_error_prefix, '')
        _, field = field.split('.', 1)
        return '{} already exists'.format(field)
    return 'Database integrity error'

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

def query_db(query, args=(), one=False):
    """
    Helper to query DB
    http://flask.pocoo.org/docs/1.0/patterns/sqlite3/
    """
    cur = get_db().execute(query, args)
    result = cur.fetchall()
    cur.close()
    return (result[0] if result else None) if one else result

def password_check(app, req):
    """
    Calls superuser_password_check() if "superuserpassword" POST parameter is
    set, user_password_check() otherwise
    """
    if 'superuserpassword' in req.form:
        return superuser_password_check(app, req)

    return user_password_check(app, req)

def user_password_check(app, req):
    """
    Helper to check username and password, taken from "name" and "password"
    POST parameters. Returns (id, name) tuple.
    """
    try:
        name = req.form['name']
        account = query_db('SELECT id, password_hash FROM accounts WHERE name = ?',
                           [name], one=True)
        if 'password' not in req.form:
            app.logger.info('password check failed: no password given')
            raise KeyError()
    except KeyError:
        app.logger.info('password check failed: no username given')
        raise KeyError('Incomplete request')

    try:
        account_id, password_hash = tuple(account)
    except TypeError:
        app.logger.info('password check failed: no such account "%s" in database', name)
        raise TypeError('No such account in database')

    if not check_password_hash(password_hash, req.form['password']):
        app.logger.info('password check failed: wrong password for account "%s"', name)
        raise ValueError('Wrong password')

    return (account_id, name)

def superuser_password_check(app, req, account_check=True):
    """
    Helper to check superuser password and account name/code, taken from
    superuserpassword", "name"/"account_code" POST parameters. Sets POST
    parameter "name" for easier post-processing. Returns (id, name) tuple.
    """
    if req.form['superuserpassword'] != \
        CONF.get('DEFAULT', 'superuser-password'):
        app.logger.warning('Account modification with wrong super user password')
        raise ValueError('Wrong superuserpassword')

    try:
        if 'name' in req.form:
            account = query_db('SELECT id, name FROM accounts WHERE name=?', [req.form['name']],
                               one=True)
        elif 'account_code' in req.form:
            account = query_db('SELECT id, name FROM accounts WHERE barcode=?',
                               [req.form['account_code']], one=True)
    except BadRequestKeyError:
        app.logger.info('superuser password check failed: no name or account_code given')
        raise KeyError('Incomplete request')

    if account_check and account is None:
        exc_str = 'No such account in database'
        app.logger.warning(exc_str)
        raise TypeError(exc_str)

        return tuple(account)
