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
import os
import subprocess
from Gcode import Gcode


class Pipe:
    def __init__(self, printer, prot):
        self.printer = printer
        self.prot = prot

        pipe_0 = "/dev/" + self.prot + "_0"
        pipe_1 = "/dev/" + self.prot + "_1"

        # Ensure tty0tty is installed and available in the PATH
        if find_executable("tty0tty") is None:
            logging.error("tty0tty not found! tty0tty must be installed")
            raise EnvironmentError("tty0tty not found")

        p = subprocess.Popen(["tty0tty", pipe_0, pipe_1],
                             stderr=subprocess.PIPE)
        p.stderr.readline()
        self.fifo = os.open(pipe_0, os.O_RDWR)
        logging.info("Pipe " + self.prot + " open. Use '" + pipe_1 + "' to "
                     "communicate with it")

        self.running = True
        self.t = Thread(target=self.get_message)
        self.send_response = True
        self.t.daemon = True
        self.t.start()

    def get_message(self):
        """ Loop that gets messages and pushes them on the queue """
        while self.running:
            ret = select.select([self.fifo], [], [], 1.0)
            if ret[0] == [self.fifo]:
                message = self.readline_custom()
                if len(message) > 0:
                    g = Gcode({"message": message, "prot": self.prot})
                    if self.printer.processor.is_buffered(g):
                        self.printer.commands.put(g)
                    else:
                        self.printer.unbuffered_commands.put(g)

    def send_message(self, message):
        if self.send_response:
            if message[-1] != "\n":
                message += "\n"
                os.write(self.fifo, message)

    def close(self):
        self.running = False
        self.t.join()
        self.fifo.close()

    def readline_custom(self):
        message = ""

        while True:
            cur_char = os.read(self.fifo, 1)
            #Check for newline char    
            if cur_char == '\n' or cur_char == "":
                return message;
            message += cur_char
