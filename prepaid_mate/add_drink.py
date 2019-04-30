#!/usr/bin/env python3
"""Add drink script."""

import os
import sys
import readline
from configparser import ConfigParser

import requests

def rlinput(prompt, prefill=''):
   readline.set_startup_hook(lambda: readline.insert_text(prefill))
   try:
      return input(prompt)
   finally:
      readline.set_startup_hook()


def add_drink(config, name, content_ml, price, barcode):
    """
    Sets the password of account "account_name" to "new_password". The config
    file is used to retrieve the API URL.
    """
    api_url = config.get('DEFAULT', 'api-url')
    superuser_pw = config.get('DEFAULT', 'superuser-password')

    data = {
        'superuserpassword': superuser_pw,
        'name': name,
        'content_ml': content_ml,
        'price': price,
        'barcode': barcode,
    }
    try:
        req = requests.post('{}/api/add_drink'.format(api_url), data=data)
    except Exception as exc:
        print(exc)
        return 1

    if req.status_code == 200:
        print('Drink added successfully')
        return 0
    if req.status_code == 400:
        print('Error: {}'.format(req.content.decode('utf-8')))
        return 1

    print('backend error: {}'.format(req.content.decode('utf-8')))
    return 1

def get_last_unknown_code(config):
    api_url = config.get('DEFAULT', 'api-url')
    req = requests.get('{}/api/last_unknown_code'.format(api_url))
    return req.content.decode('utf-8')

def main():
    """Start scanner client with ./config"""
    # assuming we can strip 'bin' and the venv directory to get the config directory
    conf_dir = os.path.join(os.path.dirname(sys.argv[0]), '..', '..')
    conf_path = os.path.join(conf_dir, './config')
    conf_file = os.environ.get('CONFIG', conf_path)

    config = ConfigParser()
    config.read_file(open(conf_file))

    barcode = rlinput('barcode: ', get_last_unknown_code(config))
    name = input('name: ')
    content_ml = input('content (in ml): ')
    price = input('price (in Cents): ')

    confirm = input('Everything correct? (y/n) ')
    if confirm != 'y':
        exit(1)

    try:
        exit(add_drink(config, name, content_ml, price, barcode))
    except FileNotFoundError:
        print('Config file not found ({}), set path via CONFIG env variable.'.format(conf_dir))
        exit(1)

if __name__ == '__main__':
    main()
