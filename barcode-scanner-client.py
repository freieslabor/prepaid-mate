#!/usr/bin/env python3

import logging
from enum import Enum, auto
import urllib.request
import urllib.parse
import urllib.error

from evdev import InputDevice, categorize, ecodes

PASSWORD = 'PROVIDE_PASSWORD_HERE'
RESET_BARCODE = '123456789'
DEBUG = False

class Mode(Enum):
    USER = auto()
    ORDER = auto()


class BarcodeScannerClient:
    def __init__(self, event_path, callback_url, callback_data, debug=False):
        self.dev = InputDevice(event_path)
        self.callback_url = callback_url
        self.callback_data = callback_data
        self.debug = debug
        self.mode = Mode.USER
        self.user = None

        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger()

    def process_barcode(self, barcode):
        if self.mode is Mode.USER:
            self.process_barcode_user(barcode)
            self.mode = Mode.ORDER
        elif self.mode is Mode.ORDER:
            if barcode == RESET_BARCODE:
                return
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
        data['user_name'] = self.user
        data = urllib.parse.urlencode(data)
        data = data.encode('ascii')
        self.logger.debug('Calling %s with %s', self.callback_url, data)
        try:
            with urllib.request.urlopen(self.callback_url, data) as f:
                self.logger.info('callback successfull: %s',
                                 f.read().decode('utf-8'))
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
    client = BarcodeScannerClient(
            '/dev/input/by-path/pci-0000:00:14.0-usb-0:2:1.0-event-kbd',
            'http://localhost:5000/api/payment/perform',
            {'password': PASSWORD},
            debug=DEBUG
            )
    client.run()
