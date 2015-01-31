#!/usr/bin/env python
"""
USB communication file for Replicape.

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
import select
import logging
from Gcode import Gcode


class USB:
    def __init__(self, printer):
        self.printer = printer
        try:
            self.tty = open("/dev/ttyGS0", "r+")
        except IOError:
            logging.warning("USB gadget serial not available as /dev/ttyGS0")
            return
        self.running = True
        self.debug = 0
        self.t = Thread(target=self.get_message)
        self.t.start()		

    def get_message(self):
        """ Loop that gets messages and pushes them on the queue """
        while self.running:
            ret = select.select([self.tty], [], [], 1.0)
            if ret[0] == [self.tty]:
                message = self.tty.readline().strip("\n")
                if len(message) > 0:
                    g = Gcode({"message": message, "prot": "USB"})
                    self.printer.processor.enqueue(g)

    def send_message(self, message):
        """ Send a message """
        if message[-1] != "\n":
            message += "\n"
        self.tty.write(message)

    def close(self):
        """ Stop receiving messages """
        self.running = False
        if hasattr(self, 't'):
            self.t.join()
