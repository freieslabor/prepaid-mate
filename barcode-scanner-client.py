#!/usr/bin/env python3

import logging
from enum import Enum, auto
import urllib.request
import urllib.parse
import urllib.error
from configparser import ConfigParser

from evdev import InputDevice, categorize, ecodes

class Mode(Enum):
    USER = auto()
    ORDER = auto()


class BarcodeScannerClient:
    def __init__(self, config_file, conf_section='barcode-scanner-client'):
        conf = ConfigParser()
        conf.read_file(open(config_file))
        self.debug = conf.getboolean(conf_section, 'debug')
        self.dev = InputDevice(conf.get(conf_section, 'scanner-device'))
        self.reset_barcode = conf.get(conf_section, 'reset-barcode')
        self.pay_callback_url = conf.get(conf_section, 'callback')
        self.callback_data = {
            'superuserpassword': conf.get('DEFAULT', 'superuser-password'),
        }
        self.mode = Mode.USER
        self.user = None

        loglevel = logging.DEBUG if logging.DEBUG else logging.INFO
        logging.basicConfig(level=loglevel)
        self.logger = logging.getLogger()

    def process_barcode(self, barcode):
        if self.mode is Mode.USER:
            self.process_barcode_user(barcode)
            self.mode = Mode.ORDER
        elif self.mode is Mode.ORDER:
            if barcode == self.reset_barcode:
                self.logger.info('reset barcode recognized, ignoring order')
            else:
                self.process_barcode_order(barcode)
            self.mode = Mode.USER

    def process_barcode_user(self, user_barcode):
        self.user = user_barcode
        self.logger.info("user barcode: %s", self.user)

    def process_barcode_order(self, order_barcode):
        assert self.user is not None
        self.logger.info('user "%s" ordered "%s"', self.user, order_barcode)
        data = self.callback_data
        data['drink_barcode'] = order_barcode
        data['name'] = self.user
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
        try:
            if not self.debug:
                self.dev.grab()
            for input_ in self.dev.read_loop():
                event = categorize(input_)
                if input_.type == ecodes.EV_KEY and event.keystate == 1:
                    if event.keycode[4:].isdigit():
                        barcode += event.keycode[4:]
                    elif event.keycode == 'KEY_ENTER':
                        self.process_barcode(barcode)
                        barcode = ''
        finally:
            if not self.debug:
                self.dev.ungrab()


if __name__ == '__main__':
    client = BarcodeScannerClient('./config')
    client.run()
