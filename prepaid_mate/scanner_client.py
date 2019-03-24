#!/usr/bin/env python3
"""Client connecting to flask application server triggering payments."""

import logging
import os
import subprocess
from enum import Enum
from configparser import ConfigParser
import select
import time
import json

import requests
from evdev import InputDevice, categorize, ecodes

class UserError(Exception):
    """Errors the user is responsible for."""

class BackendError(Exception):
    """Backend did not behave as expected."""

class Mode(Enum):
    """Modes the ScannerClient can be in."""
    ACCOUNT = 1
    ORDER = 2

class ScannerClient:
    """
    Performs payment of a drink in behave of a user.
    A user is identified by barcode or RFID code.
    A drink is always identified by barcode.
    """
    CONF_SECTION = 'scanner-client'

    def __init__(self, config_file):
        self.conf = ConfigParser()
        self.conf.read_file(open(config_file))
        self.debug = self.conf.getboolean(ScannerClient.CONF_SECTION, 'debug')
        self.api_url = self.conf.get('DEFAULT', 'api-url')
        self.mode = Mode.ACCOUNT
        self.account_code = None
        self.order_time = None

        loglevel = logging.DEBUG if self.debug else logging.INFO
        logging.basicConfig(level=loglevel)
        self.logger = logging.getLogger()

    def log_and_speak(self, msg, level=logging.INFO):
        """Logs the given message and uses espeak to inform the user"""
        self.logger.log(level, msg)
        if not self.debug:
            espeak_call = self.conf.get(ScannerClient.CONF_SECTION, 'espeak-call')
            subprocess.call(espeak_call.format(msg=msg), shell=True)

    def process_code(self, barcode, timeout=15):
        """
        Processes user barcode/RFID code and drink barcode, depending on the
        mode currenly active.
        In case timeout is exceeded between user code and drink code user code
        recognition mode is entered.
        """
        if self.order_time and time.time() > self.order_time + timeout:
            self.logger.info('order timeout, back in account scan mode')
            self.reset()

        if self.mode is Mode.ACCOUNT:
            self.process_code_account(barcode)
            self.mode = Mode.ORDER
        elif self.mode is Mode.ORDER:
            if barcode == self.conf.get(ScannerClient.CONF_SECTION, 'reset-barcode'):
                self.log_and_speak('reset barcode recognized, ignoring order')
            else:
                self.process_barcode_order(barcode)
            self.mode = Mode.ACCOUNT

    def process_code_account(self, account_code):
        """Saves the account code and remembers when it was recognized."""
        self.account_code = account_code
        self.logger.info('account code: %s', self.account_code)

        data = {'code': self.account_code}
        req = requests.post('{}/api/account/code_exists'.format(self.api_url), data=data)
        if req.status_code != 200:
            raise BackendError('backend error during account verification')

        status, name = json.loads(req.content.decode('utf-8'))
        if status:
            self.log_and_speak('hi {name}'.format(name=name))
        else:
            raise UserError('account not recognized, register now')

        self.order_time = time.time()

    def process_barcode_order(self, order_barcode):
        """
        Submit the saved account code along with the order barcode to the API.
        """
        assert self.account_code is not None
        self.logger.info('account "%s" ordered "%s"', self.account_code, order_barcode)
        data = {'superuserpassword': self.conf.get('DEFAULT', 'superuser-password')}
        data['drink_barcode'] = order_barcode
        data['account_code'] = self.account_code

        self.logger.debug('calling API with %s', data)
        req = requests.post('{}/api/payment/perform'.format(self.api_url), data=data)

        if req.status_code == 200:
            self.logger.info('callback successful: %s', req.content.decode('utf-8'))
            saldo = int(req.content.decode('utf-8'))/100.0
            self.log_and_speak('Payment successful: your balance is {} Euro' \
                               .format(saldo))
        elif req.status_code == 400:
            self.logger.error('callback failed: %s (%d)', req.content.decode('utf-8'),
                              req.status_code)
            raise UserError('Payment failed: {}'.format(req.content.decode('utf-8')))
        else:
            raise BackendError('backend error during payment')

    def reset(self):
        """Resets order specifics."""
        self.mode = Mode.ACCOUNT
        self.account_code = None
        self.order_time = None

    def run(self):
        """Endless loop grabbing content from barcode and RFID scanner."""
        scan_dev = InputDevice(self.conf.get(ScannerClient.CONF_SECTION, 'barcode-device'))
        rfid_dev = InputDevice(self.conf.get(ScannerClient.CONF_SECTION, 'rfid-device'))
        code = ''
        try:
            if not self.debug:
                scan_dev.grab()
                rfid_dev.grab()

            self.logger.info('Prepaid Mate up and running')

            while True:
                readable_dev, _, _ = select.select([scan_dev, rfid_dev], [], [])
                for dev in readable_dev:
                    input_ = dev.read_one()
                    event = categorize(input_)
                    if input_.type != ecodes.EV_KEY or event.keystate != 1:  # pylint: disable=no-member
                        continue

                    key = event.keycode.replace('KEY_', '')
                    if key.isdigit():
                        code += key
                    elif key == 'ENTER':
                        try:
                            self.process_code(code)
                        except (UserError, BackendError,
                                requests.exceptions.ConnectionError) as exc:
                            self.log_and_speak(exc.args[0], level=logging.ERROR)
                            self.reset()
                            continue
                        finally:
                            code = ''
                    else:
                        self.logger.warning('got unexpected %s from %s', event.keycode, dev)
        finally:
            if not self.debug:
                scan_dev.ungrab()
                rfid_dev.ungrab()


def main():
    """Start scanner client with ./config"""
    conf_file = os.environ.get('CONFIG', './config')
    client = ScannerClient(conf_file)
    client.run()

if __name__ == '__main__':
    main()
