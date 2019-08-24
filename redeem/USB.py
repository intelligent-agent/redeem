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
from .Gcode import Gcode


class USB:
  def __init__(self, printer, iomanager):
    self.printer = printer
    self.iomanager = iomanager
    self.send_response = False
    try:
      self.tty = open("/dev/ttyGS0", "r+")
    except IOError:
      logging.warning("USB gadget serial not available as /dev/ttyGS0")
      return
    self.iomanager.add_file(self.tty, self.get_message)

  def get_message(self):
    message = self.tty.readline().strip("\n")
    if len(message) > 0:
      g = Gcode({"message": message, "prot": "USB"})
      self.printer.processor.enqueue(g)
      # Do not enable sending messages until a
      # message has been received
      self.send_response = True

  def send_message(self, message):
    """ Send a message """
    if self.send_response:
      if message[-1] != "\n":
        message += "\n"
      #logging.debug("USB: "+str(message))
      self.tty.write(message)

  def close(self):
    """ Stop receiving messages """
    if hasattr(self, 'tty'):
      self.iomanager.remove_file(self.tty)
