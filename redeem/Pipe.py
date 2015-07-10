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
from Gcode import Gcode


class Pipe:

    @staticmethod
    def check_tty0tty():
        return (find_executable("tty0tty") is not None)

    @staticmethod
    def check_socat():
        return (find_executable("socat") is not None)

    def __init__(self, printer, prot):
        self.printer = printer
        self.prot = prot

        pipe_0 = "/dev/" + prot + "_0"
        pipe_1 = "/dev/" + prot + "_1"

        # Ensure tty0tty is installed and available in the PATH
        if not Pipe.check_tty0tty() and not Pipe.check_socat():
            logging.error("Neither tty0tty nor socat found! tty0tty or socat must be installed")
            raise EnvironmentError("tty0tty and socat not found")

        if Pipe.check_tty0tty():
            p = subprocess.Popen(["tty0tty", pipe_0, pipe_1],
                                 stderr=subprocess.PIPE)
            p.stderr.readline()

        elif Pipe.check_socat():
            p = subprocess.Popen([
                "socat", "-d", "-d", "-lf", "/var/log/redeem2"+self.prot, 
                "pty,mode=777,raw,echo=0,link="+pipe_0,
                "pty,mode=777,raw,echo=0,link="+pipe_1],
                                 stderr=subprocess.PIPE)
            while not os.path.exists(pipe_0):
                time.sleep(0.1)
        self.rd = open(pipe_0, "r")
        self.wr = os.open(pipe_0, os.O_WRONLY)
        logging.info("Pipe " + self.prot + " open. Use '" + pipe_1 + "' to "
                     "communicate with it")

        self.running = True
        self.t = Thread(target=self.get_message)
        self.send_response = True
        self.t.start()

    def get_message(self):
        """ Loop that gets messages and pushes them on the queue """
        while self.running:
            r, w, x = select.select([self.rd], [], [], 1.0)
            if r:
                message = self.rd.readline().rstrip()
                if len(message) > 0:
                    g = Gcode({"message": message, "prot": self.prot})
                    self.printer.processor.enqueue(g)

    def send_message(self, message):
        if self.send_response:
            if message[-1] != "\n":
                message += "\n"
                try:
                    os.write(self.wr, message)
                except OSError:
                    logging.warning("Unable to write to file. Closing down?")

    def close(self):
        self.running = False
        self.t.join()
        self.rd.close()
        os.close(self.wr)
