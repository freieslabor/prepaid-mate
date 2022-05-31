#!/usr/bin/env python3
"""Client connecting to flask application server triggering payments."""

import logging
import os
import subprocess
from enum import Enum
import configparser
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
    Performs payment of a drink in behalf of a user.
    A user is identified by barcode or RFID code.
    A drink is always identified by barcode.
    """
    CONF_SECTION = 'scanner-client'
    PAYMENT_SUCCEEDED_AUDIO = 'payment_success.wav'
    PAYMENT_FAILED_AUDIO = 'payment_failed.wav'

    def __init__(self, config_file):
        self.conf = configparser.ConfigParser()
        self.conf.read_file(open(config_file))
        self.debug = self.conf.getboolean(ScannerClient.CONF_SECTION, 'debug')
        self.api_url = self.conf.get('DEFAULT', 'api-url')
        self.mode = Mode.ACCOUNT
        self.account_code = None
        self.order_time = None
        self.add_balance_codes = {}

        loglevel = logging.DEBUG if self.debug else logging.INFO
        logging.basicConfig(level=loglevel)
        self.logger = logging.getLogger()

        self.parse_add_balance_codes()

    def log_and_speak(self, msg, level=logging.INFO):
        """Logs the given message and uses espeak to inform the user"""
        self.logger.log(level, msg)
        if not self.debug:
            espeak_call = self.conf.get(ScannerClient.CONF_SECTION, 'espeak-call')
            subprocess.Popen(espeak_call.format(msg=msg), shell=True)

    def do_greet(self, name, max_size=480*1024):
        """
        If a wav named after the ID of the user is found and this wav does not exceed the max_size
        play that instead of the common espeak greeting.
        """
        greet_wav = '{}.wav'.format(self.account_code)
        try:
            stat_size = os.stat(greet_wav).st_size
        except FileNotFoundError:
            stat_size = 0

        if os.path.isfile(greet_wav) and stat_size <= max_size:
            self.logger.info('playing {} as greeting for {}'.format(greet_wav, name))
            greet_call = self.conf.get(ScannerClient.CONF_SECTION, 'play-call')
            subprocess.Popen(greet_call.format(wav=greet_wav), shell=True)
        else:
            if os.path.isfile(greet_wav):
                self.logger.info('{} ({} bytes) exceeds maximum size ({} bytes), using espeak'
                                 .format(greet_wav, stat_size, max_size))

            self.log_and_speak('hi {name}'.format(name=name))

    def play_status_sound(self, wav):
        if os.path.isfile(wav):
            play_call = self.conf.get(ScannerClient.CONF_SECTION, 'play-call')
            # intentional blocking call for short status sound
            subprocess.call(play_call.format(wav=wav), shell=True)

    def cents_to_natural_speech(self, amount):
        amount = int(amount)
        amount = str(round(amount/100)) if amount % 100 == 0 else str(amount/100)

        return '{} Euro'.format(amount)

    def parse_add_balance_codes(self):
        """
        Parses config "<amount>-eur-code" codes and stores them in self.add_balance_codes dict.
        """
        for amount in range(1000):
            try:
                option = '{}-eur-code'.format(amount)
                code = self.conf.get(ScannerClient.CONF_SECTION, option)
            except configparser.NoOptionError:
                continue

            if code in self.add_balance_codes:
                raise UserError('Forbidden duplicate in add balance codes, check your config')

            self.add_balance_codes[code] = amount

    def add_balance(self, amount):
        """Adds given amount to the user's balance."""

        data = {
            'superuserpassword': self.conf.get('DEFAULT', 'superuser-password'),
            'account_code': self.account_code,
            'money': amount*100,
        }
        req = requests.post('{}/api/money/add'.format(self.api_url), data=data)

        if req.status_code == 200:
            self.logger.info('add balance callback successful: %s', req.content.decode('utf-8'))
            self.play_status_sound(ScannerClient.PAYMENT_SUCCEEDED_AUDIO)
            saldo = self.cents_to_natural_speech(req.content.decode('utf-8'))
            self.log_and_speak('Added {} Euro, your balance is {}'.format(amount, saldo_speech))
        elif req.status_code == 400:
            self.logger.error('add balance callback failed: %s (%d)', req.content.decode('utf-8'),
                              req.status_code)
            raise UserError('Adding money failed: {}'.format(req.content.decode('utf-8')))
        else:
            raise BackendError('backend error during adding money')


    def process_code(self, barcode, timeout=15):
        """
        Processes user barcode/RFID code and drink barcode, depending on the
        mode currenly active.
        In case timeout is exceeded between user code and drink code user code
        recognition mode is entered.
        """
        if barcode in self.add_balance_codes:
            if self.mode is Mode.ACCOUNT:
                raise UserError('Please identify first.')

            self.add_balance(self.add_balance_codes[barcode])
            self.reset()
            return

        if barcode == self.conf.get(ScannerClient.CONF_SECTION, 'speak-balance-code'):
            if self.mode is Mode.ACCOUNT:
                raise UserError('Please identify first.')

            data = {'code': self.account_code}
            req = requests.post('{}/api/account/code_exists'.format(self.api_url), data=data)
            if req.status_code != 200:
                raise BackendError('backend error during balance retrieval')

            status, _, saldo = json.loads(req.content.decode('utf-8'))
            assert status is True
            saldo = self.cents_to_natural_speech(saldo)
            self.log_and_speak('Your balance is {}'.format(saldo))
            self.reset()

        if self.order_time and time.time() > self.order_time + timeout:
            self.logger.info('order timeout, back in account scan mode')
            self.reset()

        if self.mode is Mode.ACCOUNT:
            if self.process_code_account(barcode):
                self.mode = Mode.ORDER
        elif self.mode is Mode.ORDER:
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

        status, name, _ = json.loads(req.content.decode('utf-8'))
        if status:
            self.do_greet(name)
        else:
            req = requests.post('{}/api/drink/view'.format(self.api_url), data={'barcode': self.account_code})
            if req.status_code == 200:
                name, _, price = json.loads(req.content.decode('utf-8'))
                price = self.cents_to_natural_speech(price)
                self.log_and_speak('Enjoy a cool {}, only {}'.format(name, price))
                self.reset()
                return False

            raise UserError('code not recognized, register now')

        self.order_time = time.time()
        return True

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
            self.logger.info('order callback successful: %s', req.content.decode('utf-8'))
            self.play_status_sound(ScannerClient.PAYMENT_SUCCEEDED_AUDIO)
            saldo = self.cents_to_natural_speech(req.content.decode('utf-8'))
            self.log_and_speak('Payment successful: your balance is {}'.format(saldo))
        elif req.status_code == 400:
            self.logger.error('order callback failed: %s (%d)', req.content.decode('utf-8'),
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
                            if dev == rfid_dev:
                                # hacky state machine shortcut
                                self.process_code_account(code)
                                self.mode = Mode.ORDER
                            else:
                                self.process_code(code)
                        except (UserError, BackendError,
                                requests.exceptions.ConnectionError) as exc:
                            self.log_and_speak(exc.args[0], level=logging.ERROR)
                            self.play_status_sound(ScannerClient.PAYMENT_FAILED_AUDIO)
                            self.reset()
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
