#!/usr/bin/env python3

import logging
import os
from enum import Enum
from configparser import ConfigParser
import select
import time

import requests
from evdev import InputDevice, categorize, ecodes

class Mode(Enum):
    ACCOUNT = 1
    ORDER = 2


class BarcodeScannerClient:
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
        self.account_barcode = None
        self.order_time = None

        loglevel = logging.DEBUG if logging.DEBUG else logging.INFO
        logging.basicConfig(level=loglevel)
        self.logger = logging.getLogger()

    def log_and_speak(self, msg):
        self.logger.info(msg)
        os.system('/usr/bin/espeak "{msg}"', msg=msg)

    def process_barcode(self, barcode, timeout=15):
        if self.order_time and time.time() > self.order_time + timeout:
            self.log_and_speak('order timeout, back in account scan mode')
            self.mode = Mode.ACCOUNT

        if self.mode is Mode.ACCOUNT:
            self.process_barcode_account(barcode)
            self.mode = Mode.ORDER
        elif self.mode is Mode.ORDER:
            if barcode == self.reset_barcode:
                self.log_and_speak('reset barcode recognized, ignoring order')
            else:
                self.process_barcode_order(barcode)
            self.mode = Mode.ACCOUNT

    def process_barcode_account(self, account_barcode):
        self.account_barcode = account_barcode
        self.logger.info('account barcode: %s', self.account_barcode)
        self.order_time = time.time()

    def process_barcode_order(self, order_barcode):
        assert self.account_barcode is not None
        self.logger.info('account "%s" ordered "%s"', self.account_barcode, order_barcode)
        data = self.callback_data
        data['drink_barcode'] = order_barcode
        data['account_barcode'] = self.account_barcode

        self.logger.debug('calling %s with %s', self.pay_callback_url, data)
        r = requests.post(self.pay_callback_url, data=data)

        if r.status_code == 200:
            self.logger.info('callback successful: %s', r.content.decode('utf-8'))
            saldo = int(r.content.decode('utf-8'))/100.0
            self.log_and_speak('Payment successful: your balance is {} Euro' \
                               .format(saldo))
        else:
            self.logger.error('callback failed: %s (%d)', r.content.decode('utf-8'), r.status_code)
            self.log_and_speak('Payment failed: {}'.format(r.content.decode('utf-8')))

    def run(self):
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
                    if input_.type == ecodes.EV_KEY and event.keystate == 1:
                        if event.keycode[4:].isdigit():
                            if dev == self.scan_dev:
                                barcode += event.keycode[4:]
                            elif dev == self.rfid_dev:
                                rfid += event.keycode[4:]
                        elif event.keycode == 'KEY_ENTER':
                            if dev == self.scan_dev:
                                self.process_barcode(barcode)
                                barcode = ''
                            elif dev == self.rfid_dev:
                                self.process_barcode(rfid)
                                rfid = ''
        finally:
            if not self.debug:
                self.scan_dev.ungrab()
                self.rfid_dev.ungrab()


if __name__ == '__main__':
    conf_file = os.environ.get('CONFIG', './config')
    client = BarcodeScannerClient(conf_file)
    client.run()
