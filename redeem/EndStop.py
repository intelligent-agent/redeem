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

import logging
import re
from evdev import InputDevice
from .Key_pin import Key_pin
from .PruInterface import PruInterface


class EndStop:
  def __init__(self, printer, pin, key_code, name, invert=False):
    self.printer = printer
    self.pin = pin
    self.key_code = key_code
    self.invert = invert
    self.dev = InputDevice(EndStop.inputdev)

    self.name = name
    if name == "X1":
      self.condition_bit = (1 << 0)
    elif name == "Y1":
      self.condition_bit = (1 << 1)
    elif name == "Z1":
      self.condition_bit = (1 << 2)
    elif name == "X2":
      self.condition_bit = (1 << 3)
    elif name == "Y2":
      self.condition_bit = (1 << 4)
    elif name == "Z2":
      self.condition_bit = (1 << 5)
    else:
      raise RuntimeError('Invalid endstop name')

    # Update "hit" state
    self.read_value()

    logging.debug("starting endstop %s", self.name)

    self.key_pin = Key_pin(self.name + "_pin", self.key_code, 0xff, self._handle_event)
    self.active = True

  def get_gpio_bank_and_pin(self):
    matches = re.compile(r'GPIO([0-9])_([0-9]+)').search(self.pin)
    tup = matches.group(1, 2)
    tup = (int(tup[0]), int(tup[1]))
    return tup

  def stop(self):
    logging.debug("End stop {} stopping".format(self.name))

  def get_pin(self):
    return self.pin

  def _handle_event(self, key, event):
    if self.invert:
      if int(event.value):
        self.hit = True
      else:
        self.hit = False
    elif not self.invert:
      if not int(event.value):
        self.hit = True
      else:
        self.hit = False
    self.callback()

  def read_value(self):
    """ Read the current endstop value from GPIO using PRU1 """
    state = PruInterface.get_shared_long(0)
    self.hit = bool(state & self.condition_bit)

  def callback(self):
    """ An endStop has changed state """
    type_string = "hit" if self.hit else "released"
    event_string = "End Stop {} {}!".format(self.name, type_string)
    logging.info(event_string)
    for channel in ["octoprint", "toggle"]:
      if channel in self.printer.comms:
        self.printer.comms[channel].send_message(event_string)


if __name__ == "__main__":
  print("Test endstops")

  import time

  while True:
    state = PruInterface.get_shared_long(0)
    print(bin(state) + "  ", )
    if bool(state & (1 << 0)):
      print("X1", )
    elif bool(state & (1 << 1)):
      print("Y1", )
    elif bool(state & (1 << 2)):
      print("Z1", )
    elif bool(state & (1 << 3)):
      print("X2", )
    elif bool(state & (1 << 4)):
      print("Y2", )
    elif bool(state & (1 << 5)):
      print("Z2", )
    print((" " * 30) + "\r", )
    time.sleep(0.01)
