"""
Pipe - This uses a virtual TTY for communicating with
Toggle or similar front end.

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

import errno
import fcntl
import logging
import os
import select
import subprocess
import termios
import time
from Gcode import Gcode
from threading import Thread


class Pipe:
  def __init__(self, printer, prot, iomanager):
    self.printer = printer
    self.prot = prot
    self.iomanager = iomanager

    (master_fd, slave_fd) = os.openpty()
    slave = os.ttyname(slave_fd)

    master_flags = fcntl.fcntl(master_fd, fcntl.F_GETFL, 0)
    fcntl.fcntl(master_fd, fcntl.F_SETFL, master_flags | os.O_NONBLOCK)

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

    logging.info("Opened PTY for {} and got {}".format(prot, os.ttyname(slave_fd)))

    self.pipe_link = "/dev/" + prot + "_1"

    try:
      os.unlink(self.pipe_link)
    except OSError, e:
      # file not found is fine to ignore - anythine else and we should log it
      if e.errno != errno.ENOENT:
        logging.error("Failed to unlink '{}': {}".format(self.pipe_link, e.strerror))

    logging.info("linking {}".format(self.pipe_link))
    os.symlink(slave, self.pipe_link)
    os.chmod(self.pipe_link, 0o666)

    logging.info("{} Pipe open. Use '{}' to communicate with it".format(self.prot, self.pipe_link))

    self.rd = os.fdopen(master_fd, "r")
    self.wr = os.fdopen(master_fd, "w")

    self.send_response = True
    self.iomanager.add_file(self.rd, self.get_message)

  def get_message(self, flags):
    try:
      message = self.rd.readline().rstrip()
      if len(message) > 0:
        g = Gcode({"message": message, "prot": self.prot})
        self.printer.processor.enqueue(g)
    except IOError:
      logging.warning("Could not read from {} pipe".format(self.prot))

  def send_message(self, message):
    if self.send_response:
      #logging.debug("Pipe: "+str(message))
      if message[-1] != "\n":
        message += "\n"
        try:
          self.wr.write(message)
        except OSError:
          logging.warning("Unable to write to {} pipe".format(self.prot))
        except IOError as error:
          if error.errno != errno.EAGAIN:    # if the output buffer is full, we're just going to drop messages
            logging.warning("Failed to write to file: %s", error)

  def close(self):
    self.iomanager.remove_file(self.rd)
    self.rd.close()
    os.unlink(self.pipe_link)
