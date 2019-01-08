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
from evdev import InputDevice, ecodes
from PruInterface import *
from select import select
from threading import Thread


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

    self.running = True
    self.t = Thread(target=self._wait_for_event, name=self.name)
    self.t.daemon = True
    self.active = True
    self.t.start()

  def get_gpio_bank_and_pin(self):
    matches = re.compile(r'GPIO([0-9])_([0-9]+)').search(self.pin)
    tup = matches.group(1, 2)
    tup = (int(tup[0]), int(tup[1]))
    return tup

  def stop(self):
    self.running = False
    logging.debug("End stop {} stopping".format(self.name))
    self.t.join()

  def get_pin(self):
    return self.pin

  def _wait_for_event(self):
    while self.running:
      #logging.debug("End stop {} waiting".format(self.name))
      r, w, x = select([self.dev], [], [], 3)
      if r:
        #logging.debug("End stop {} event".format(self.name))
        for event in self.dev.read():
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
      #else:
      #    logging.debug("End stop {} timeout".format(self.name))

  def read_value(self):
    """ Read the current endstop value from GPIO using PRU1 """
    state = PruInterface.get_shared_long(0)
    self.hit = bool(state & self.condition_bit)

  def callback(self):
    """ An endStop has been hit """
    logging.info("End Stop " + self.name + " hit!")
    if "toggle" in self.printer.comms:
      self.printer.comms["toggle"].send_message("End stop {} hit!".format(self.name))
    if "octoprint" in self.printer.comms:
      self.printer.comms["octoprint"].send_message("End stop {} hit!".format(self.name))


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
