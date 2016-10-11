#!/usr/bin/env python
"""
Common class listening to key events. 
A callback can be registered so an even

Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: GNU GPL v3: http://www.gnu.org/copyleft/gpl.html

 Redeem is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Redeem is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Redeem.  If not, see <http://www.gnu.org/licenses/>.
"""

import time
import subprocess
import os
import logging

from threading import Thread

from evdev import *
from select import select

class Key_pin:
    RISING = 0
    FALLING = 1

    listener = None # Add this durin startup

    def __init__(self, name, key_code, edge=1, callback=None): 
        self.name = name
        self.code = key_code
        self.edge = edge
        self.callback = callback
        if Key_pin.listener:
            Key_pin.listener.add_pin(self)

    def __str__(self):
        """ For debugging. """
        return "Key_pin: {}, code: {}, edge: {} ".format(self.name, self.code, self.edge)


class Key_pin_listener:
    def __init__(self, fd):
        self.dev = InputDevice(fd)
        self.keys = {}
        self.t = Thread(target=self._run, name="Key_pin_listener")
        self.running = False

    def add_pin(self, key):
        logging.debug("Adding pin with key {}".format(key.code))
        self.keys[key.code] = key

    def start(self):
        self.running = True
        self.t.start()

    def stop(self):
        if self.running:
            logging.debug("Stoppping Key_pin_listener")
            self.running = False
            self.t.join()
        else:
            logging.debug("Attempted to stop Key_pin_listener when it is not running")

    def _run(self):
        while self.running:
            r,w,x = select([self.dev.fd], [], [], 0.5)
            if r: 
                for event in self.dev.read():
                    #logging.debug(event)
                    if event.type == ecodes.EV_KEY:
                        code = int(event.code)
                        val = int(event.value)
                        if code in self.keys:
                            key = self.keys[code]
                            if val == key.edge and key.callback:
                                key.callback(key, event)






if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')

    def callback(key_pin, event):
        logging.info("Callback for "+str(key_pin))

    Key_pin.listener = Key_pin_listener("/dev/input/event0")
    k1 = Key_pin("X1", 114, Key_pin.FALLING, callback)
    Key_pin.listener.start()

    time.sleep(5)
