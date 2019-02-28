#!/usr/bin/env python3

import logging
import os
from enum import Enum
import urllib.request
import urllib.parse
import urllib.error
from configparser import ConfigParser
import select

from evdev import InputDevice, categorize, ecodes

class Mode(Enum):
    ACCOUNT = 1
    ORDER = 2


class BarcodeScannerClient:
    def __init__(self, config_file, conf_section='scanner-client'):
        conf = ConfigParser()
        conf.read_file(open(config_file))
        self.debug = conf.getboolean(conf_section, 'debug')
        self.scan_dev = InputDevice(conf.get(conf_section, 'scanner-device'))
        self.rfid_dev = InputDevice(conf.get(conf_section, 'rfid-device'))
        self.reset_barcode = conf.get(conf_section, 'reset-barcode')
        self.pay_callback_url = conf.get(conf_section, 'callback')
        self.callback_data = {
            'superuserpassword': conf.get('DEFAULT', 'superuser-password'),
        }
        self.mode = Mode.ACCOUNT
        self.account = None

        loglevel = logging.DEBUG if logging.DEBUG else logging.INFO
        logging.basicConfig(level=loglevel)
        self.logger = logging.getLogger()

    def process_barcode(self, barcode):
        if self.mode is Mode.ACCOUNT:
            self.process_barcode_account(barcode)
            self.mode = Mode.ORDER
        elif self.mode is Mode.ORDER:
            if barcode == self.reset_barcode:
                self.logger.info('reset barcode recognized, ignoring order')
            else:
                self.process_barcode_order(barcode)
            self.mode = Mode.ACCOUNT

    def process_barcode_account(self, account_barcode):
        self.account = account_barcode
        self.logger.info("account barcode: %s", self.account)

    def process_barcode_order(self, order_barcode):
        assert self.account is not None
        self.logger.info('account "%s" ordered "%s"', self.account, order_barcode)
        data = self.callback_data
        data['drink_barcode'] = order_barcode
        data['name'] = self.account
        data = urllib.parse.urlencode(data)
        data = data.encode('ascii')
        self.logger.debug('Calling %s with %s', self.pay_callback_url, data)
        try:
            with urllib.request.urlopen(self.pay_callback_url, data) as f:
                self.logger.info('callback successfull: %s',
                                 f.read().decode('utf-8'))
                # FIXME: confirm payment and use text2speech to notify user
                # about balance
        except urllib.error.URLError as e:
            self.logger.error(e)

    def run(self):
        barcode = ''
        rfid = ''
        try:
            if not self.debug:
                self.scan_dev.grab()
                self.rfid_dev.grab()

            self.logger.info('Waiting for input..')

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
        print("ciao")


if __name__ == '__main__':
    conf_file = os.environ.get('CONFIG', './config')
    client = BarcodeScannerClient(conf_file)
    client.run()
