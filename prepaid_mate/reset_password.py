#!/usr/bin/env python3
"""Superuser password reset script."""

import os
import sys
import getpass
import hashlib
from configparser import ConfigParser

import requests

def password_reset(config_file, account_name, new_password):
        conf = ConfigParser()
        conf.read_file(open(config_file))

        api_url = conf.get('DEFAULT', 'api-url')
        superuser_pw = conf.get('DEFAULT', 'superuser-password')

        data = {
            'superuserpassword': superuser_pw,
            'name': account_name,
            'new_password': hashlib.md5(new_password.encode('utf-8')).hexdigest(),
        }
        try:
            req = requests.post('{}/api/account/modify'.format(api_url), data=data)
        except Exception as exc:
            print(exc)
            return 1

        if req.status_code == 200:
            print('Set password for "{}" successfully'.format(account_name))
            return 0
        elif req.status_code == 400:
            print('Error: {}'.format(req.content.decode('utf-8')))
            return 1
        else:
            print('backend error: {}'.format(req.content.decode('utf-8')))
            return 1

def main():
    """Start scanner client with ./config"""
    # assuming we can strip 'bin' and the venv directory to get the config directory
    conf_dir = os.path.join(os.path.dirname(sys.argv[0]), '..', '..')
    conf_path = os.path.join(conf_dir, './config')
    conf_file = os.environ.get('CONFIG', conf_path)

    if len(sys.argv) < 2:
        print('Usage: {} USER'.format(sys.argv[0]))
        exit(1)

    password = getpass.getpass('New password: ')
    try:
        exit(password_reset(conf_file, sys.argv[1], password))
    except FileNotFoundError:
        print('Config file not found ({}), set path via CONFIG env variable.'.format(conf_dir))
        exit(1)

if __name__ == '__main__':
    main()
