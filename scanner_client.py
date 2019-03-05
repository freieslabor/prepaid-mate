#!/usr/bin/env python3
"""Client connecting to flask application server triggering payments."""

import logging
import os
from enum import Enum
from configparser import ConfigParser
import select
import time

import requests
from evdev import InputDevice, categorize, ecodes

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
    def __init__(self, config_file, conf_section='scanner-client'):
        conf = ConfigParser()
        conf.read_file(open(config_file))
        self.debug = conf.getboolean(conf_section, 'debug')
        self.scan_dev = InputDevice(conf.get(conf_section, 'barcode-device'))
        self.rfid_dev = InputDevice(conf.get(conf_section, 'rfid-device'))
        self.reset_barcode = conf.get(conf_section, 'reset-barcode')
        self.pay_callback_url = conf.get(conf_section, 'callback')
        self.callback_data = {
            'superuserpassword': conf.get('DEFAULT', 'superuser-password'),
        }
        self.mode = Mode.ACCOUNT
        self.account_code = None
        self.order_time = None

        loglevel = logging.DEBUG if logging.DEBUG else logging.INFO
        logging.basicConfig(level=loglevel)
        self.logger = logging.getLogger()

    def log_and_speak(self, msg):
        """Logs the given message and uses espeak to inform the user"""
        self.logger.info(msg)
        os.system('/usr/bin/espeak "{msg}"', msg=msg)

    def process_code(self, barcode, timeout=15):
        """
        Processes user barcode/RFID code and drink barcode, depending on the
        mode currenly active.
        In case timeout is exceeded between user code and drink code user code
        recognition mode is entered.
        """
        if self.order_time and time.time() > self.order_time + timeout:
            self.log_and_speak('order timeout, back in account scan mode')
            self.mode = Mode.ACCOUNT

        if self.mode is Mode.ACCOUNT:
            self.process_code_account(barcode)
            self.mode = Mode.ORDER
        elif self.mode is Mode.ORDER:
            if barcode == self.reset_barcode:
                self.log_and_speak('reset barcode recognized, ignoring order')
            else:
                self.process_barcode_order(barcode)
            self.mode = Mode.ACCOUNT

    def process_code_account(self, account_code):
        """Saves the account code and remembers when it was recognized."""
        self.account_code = account_code
        self.logger.info('account code: %s', self.account_code)
        self.order_time = time.time()

    def process_barcode_order(self, order_barcode):
        """
        Submit the saved account code along with the order barcode to the
        defined callback.
        """
        assert self.account_code is not None
        self.logger.info('account "%s" ordered "%s"', self.account_code, order_barcode)
        data = self.callback_data
        data['drink_barcode'] = order_barcode
        data['account_code'] = self.account_code

        self.logger.debug('calling %s with %s', self.pay_callback_url, data)
        req = requests.post(self.pay_callback_url, data=data)

        if req.status_code == 200:
            self.logger.info('callback successful: %s', req.content.decode('utf-8'))
            saldo = int(req.content.decode('utf-8'))/100.0
            self.log_and_speak('Payment successful: your balance is {} Euro' \
                               .format(saldo))
        else:
            self.logger.error('callback failed: %s (%d)', req.content.decode('utf-8'),
                              req.status_code)
            self.log_and_speak('Payment failed: {}'.format(req.content.decode('utf-8')))

    def run(self):
        """Endless loop grabbing content from barcode and RFID scanner."""
        barcode = ''
        rfid = ''
        try:
            if not self.debug:
                self.scan_dev.grab()
                self.rfid_dev.grab()

            self.logger.info('Prepaid Mate up and running')

            while True:
                readable_dev, _, _ = select.select([self.scan_dev, self.rfid_dev], [], [])
                for dev in readable_dev:
                    input_ = dev.read_one()
                    event = categorize(input_)
                    if input_.type == ecodes.EV_KEY and event.keystate == 1:  # pylint: disable=no-member
                        if event.keycode[4:].isdigit():
                            if dev == self.scan_dev:
                                barcode += event.keycode[4:]
                            elif dev == self.rfid_dev:
                                rfid += event.keycode[4:]
                        elif event.keycode == 'KEY_ENTER':
                            if dev == self.scan_dev:
                                self.process_code(barcode)
                                barcode = ''
                            elif dev == self.rfid_dev:
                                self.process_code(rfid)
                                rfid = ''
        finally:
            if not self.debug:
                self.scan_dev.ungrab()
                self.rfid_dev.ungrab()


if __name__ == '__main__':
    CONF_FILE = os.environ.get('CONFIG', './config')
    CLIENT = ScannerClient(CONF_FILE)
    CLIENT.run()
