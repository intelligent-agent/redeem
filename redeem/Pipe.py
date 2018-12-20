#!/usr/bin/env python
"""
Pipe - This uses a virtual TTY for communicating with
Toggler or similar front end.

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
from distutils.spawn import find_executable
import select
import logging
import subprocess
import time
import os
import errno
import termios
from Gcode import Gcode


class Pipe:
  def __init__(self, printer, prot):
    self.printer = printer
    self.prot = prot

    (master_fd, slave_fd) = os.openpty()
    slave = os.ttyname(slave_fd)

    # switch to "raw" mode - these constants come from the manpage for termios under cfmakeraw()
    master_attr = termios.tcgetattr(master_fd)
    master_attr[0] &= ~(termios.IGNBRK | termios.BRKINT | termios.PARMRK | termios.ISTRIP
                        | termios.INLCR | termios.IGNCR | termios.ICRNL | termios.IXON)
    master_attr[1] &= ~termios.OPOST
    master_attr[2] &= ~(termios.CSIZE | termios.PARENB)
    master_attr[3] &= ~(termios.ECHO | termios.ECHONL | termios.ICANON | termios.ISIG
                        | termios.IEXTEN)
    master_attr[3] |= termios.CS8
    termios.tcsetattr(master_fd, termios.TCSADRAIN, master_attr)

    # Fun detail: master will always show as /dev/ptmx, but the kernel knows from
    # the fd which PTY we're using. This means we have to use master_fd instead
    # of opening master by name.

    logging.info("Opened PTY for " + prot + " and got " + os.ttyname(master_fd) + " and " + slave)

    self.pipe_link = "/dev/" + prot + "_1"

    self.file = os.fdopen(master_fd, "r+")

    logging.info("Unlinking " + self.pipe_link)
    try:
      os.unlink(self.pipe_link)
    except OSError, e:
      # file not found is fine to ignore - anythine else and we should log it
      if e.errno != errno.ENOENT:
        logging.error("Failed to unlink " + self.pipe_link + ": " + e.strerror)

    logging.info("re-linking " + self.pipe_link)
    os.symlink(slave, self.pipe_link)
    os.chmod(self.pipe_link, 0666)

    logging.info("Pipe " + self.prot + " open. Use '" + self.pipe_link + "' to communicate with it")

    self.running = True
    self.t = Thread(target=self.get_message, name="Pipe")
    self.send_response = True
    self.t.start()

  def get_message(self):
    """ Loop that gets messages and pushes them on the queue """
    while self.running:
      r, w, x = select.select([self.file], [], [], 1.0)
      if r:
        try:
          message = self.file.readline().rstrip()
          if len(message) > 0:
            g = Gcode({"message": message, "prot": self.prot})
            self.printer.processor.enqueue(g)
        except IOError:
          logging.warning("Could not read from pipe")

  def send_message(self, message):
    if self.send_response:
      #logging.debug("Pipe: "+str(message))
      if message[-1] != "\n":
        message += "\n"
        try:
          self.file.write(message)
        except OSError:
          logging.warning("Unable to write to file. Closing down?")

  def close(self):
    self.running = False
    self.t.join()
    self.file.close()
    os.unlink(self.pipe_link)
