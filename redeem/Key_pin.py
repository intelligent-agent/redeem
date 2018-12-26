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

import logging
from evdev import InputDevice, ecodes
import select


class Key_pin:
  RISING = 0
  FALLING = 1

  listener = None    # Add this during startup

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
  def __init__(self, fd, iomanager):
    self.dev = InputDevice(fd)
    self.iomanager = iomanager
    self.keys = {}

  def add_pin(self, key):
    logging.debug("Adding pin with key {}".format(key.code))
    self.keys[key.code] = key

  def start(self):
    logging.debug("starting Key_pin_listener")
    self.iomanager.add_file(self.dev, self._handle_event)
    self.running = True

  def stop(self):
    if self.running:
      logging.debug("Stopping Key_pin_listener")
      self.running = False
      self.iomanager.remove_file(self.dev)
    else:
      logging.debug("Attempted to stop Key_pin_listener when it is not running")

  def _handle_event(self, flags):
    logging.debug("Key_pin_listener handler start")
    if flags != select.POLLIN:
      logging.error("Key_pin_listener read failure: %s", str(flags))
      try:
        events = self.dev.read()
        logging.error("Key_pin_listener still got events: %s ?!?", str(events))
      except IOError as e:
        logging.error("Key_pin_listener read failed: %s", str(e))
      logging.error("Key_pin_listener removing key pin FD")
      self.iomanager.remove_file(self.dev)
    else:
      try:
        for event in self.dev.read():
          logging.debug("key pin event: %s", event)
          if event.type == ecodes.EV_KEY:
            code = int(event.code)
            val = int(event.value)
            if code in self.keys:
              key = self.keys[code]
              if (key.edge == 0xff or val == key.edge) and key.callback:
                logging.debug("sending key pin event to handler %s", str(key))
                key.callback(key, event)
                logging.debug("key pin event handler done")
      except IOError as e:
        logging.error("Key_pin_listener read failed in read event: %s", str(e))
        self.iomanager.remove_file(self.dev)
    logging.debug("Key_pin_listener handler end")
