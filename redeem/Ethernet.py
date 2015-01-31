#!/usr/bin/env python
"""
Ethernet communication file for Replicape.

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
import socket
import logging
from Gcode import Gcode

size = 1024 


class Ethernet:
    def __init__(self, printer):
        self.printer = printer
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = ''
        port = 50000
        backlog = 5       
        for i in range(10):
            try: 
                self.s.bind((host, port))
                break
            except socket.error:
                port += 1    

        logging.info("Ethernet bound to port " + str(port))
        self.s.listen(backlog)
        self.client = None
        self.running = True
        self.t = Thread(target=self.get_message)
        self.t.start()

    def get_message(self):
        """Loop that gets messages and pushes them on the queue"""
        while self.running:
            #logging.info("Ethernet listening")
            self.s.settimeout(1.0)
            try:
                self.client, self.address = self.s.accept()
            except IOError as e:
                continue
            logging.info("Ethernet connection accepted")
            self.s.settimeout(1.0)
            while self.running:
                line = self.read_line()
                if line is None:
                    break
                message = line.strip("\n")
                if len(message) > 0:
                    g = Gcode({"message": message, "prot": "Eth"})
                    self.printer.processor.enqueue(g)

    def send_message(self, message):
        """Send a message"""
        if message[-1] != "\n":
            message += "\n"
        try:
            self.client.send(message)
        except socket.error, (value, message):
            logging.error("Ethernet " + message)

    def read_line(self):
        """read a line from a socket"""
        chars = []
        while self.running:
            try:
                char = self.client.recv(1)
            except socket.error, (value, message):
                logging.error("Ethernet " + message)
                char = ""
            if char == "":
                logging.warning("Ethernet: Connection reset by peer.")
                self.client.close()
                break
            chars.append(char)
            if char == "\n":
                return "".join(chars)

    def close(self):
        """Stop receiving messages"""
        self.running = False
        if self.client is not None:
            self.client.shutdown(socket.SHUT_RDWR)
            self.client.close()
        self.s.shutdown(socket.SHUT_RDWR)
        self.s.close()
        self.t.join()
