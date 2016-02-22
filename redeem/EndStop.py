#!/usr/bin/env python
"""
A class that listens for a button press
and sends an event if that happens.

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

from threading import Thread
import re
from PruInterface import *
from evdev import InputDevice, ecodes

class EndStop:
    def __init__(self, printer, pin, key_code, name, invert=False):
        self.printer = printer
        self.pin = pin
        self.key_code = key_code
        self.name = name
        self.invert = invert
        self.dev = InputDevice(EndStop.inputdev)
        self.t = Thread(target=self._wait_for_event, name=self.name)
        self.t.daemon = True

        # Update "hit" state
        self.read_value()

        self.running = True
        self.t.start()

    def get_gpio_bank_and_pin(self):
        matches = re.compile(r'GPIO([0-9])_([0-9]+)').search(self.pin)
        tup = matches.group(1, 2)
        tup = (int(tup[0]), int(tup[1]))
        return tup

    def stop(self):
        self.running = False
        self.t.join()

    def get_pin(self):
        return self.pin

    def _wait_for_event(self):
        for event in self.dev.read_loop():
            if event.type == ecodes.EV_KEY:
                if event.code == self.key_code:
                    if self.invert: 
                        if int(event.value):
                            self.hit = True 
                            self.callback()
                        else:
                            self.hit = False
                    elif not self.invert:
                        if not int(event.value):
                            self.hit = True 
                            self.callback()
                        else:
                            self.hit = False
            if not self.running:
                break

    def read_value(self):
        """ Read the current endstop value from GPIO using PRU1 """
        state = PruInterface.get_shared_long(0)
        if self.name == "X1":
            self.hit = bool(state & (1 << 0))
        elif self.name == "Y1":
            self.hit = bool(state & (1 << 1))
        elif self.name == "Z1":
            self.hit = bool(state & (1 << 2))
        elif self.name == "X2":
            self.hit = bool(state & (1 << 3))
        elif self.name == "Y2":
            self.hit = bool(state & (1 << 4))
        elif self.name == "Z2":
            self.hit = bool(state & (1 << 5))
        else:
            raise RuntimeError('Invalid endstop name')
                        
    def callback(self):
        """ An endStop has been hit """
        logging.info("End Stop " + self.name + " hit!")
        if "toggle" in self.printer.comms:
            self.printer.comms["toggle"].send_message("End stop {} hit!".format(self.name))
        if "octoprint" in self.printer.comms:
            self.printer.comms["octoprint"].send_message("End stop {} hit!".format(self.name))
    
if __name__ == "__main__":
    print "Test endstops"
    
    while True:
        state = PruInterface.get_shared_long(0)
        print bin(state) + "  ", 
        if bool(state & (1 << 0)):
            print "X1",
        elif bool(state & (1 << 1)):
            print "Y1",
        elif bool(state & (1 << 2)):
            print "Z1",
        elif bool(state & (1 << 3)):
            print "X2",
        elif bool(state & (1 << 4)):
            print "Y2",
        elif bool(state & (1 << 5)):
            print "Z2",
        print (" "*30)+"\r", 
            
    
