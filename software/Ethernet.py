#!/usr/bin/env python
'''
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
'''

from threading import Thread
import socket
import logging
import select
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
                self.s.bind((host,port))
                break
            except socket.error as e:
                port += 1    

        logging.info("Ethernet bound to port "+str(port))
        self.s.listen(backlog)
        self.running = True
        self.debug = 0
        self.t = Thread(target=self.get_message)
        self.t.daemon = True
        self.t.start()		

    # Loop that gets messages and pushes them on the queue
    def get_message(self):
        while self.running:
            logging.info("Ethernet listening")
            self.client, self.address = self.s.accept()
            logging.info("Ethernet connection accepted")
            while True:
                line = ''
                while not "\n" in line:
                    try: 
                        chunk = self.client.recv(1)
                    except socket.error, (value,message): 
                        logging.error("Ethernet "+ message)
                        chunk = ''
                    if chunk == '':
                        logging.warning("Ethernet: Connection reset by Per.")
                        self.client.close()             
                        break
                    line = line + chunk
                if not "\n" in line: # Make sure the whole line was read. 
                    break
                message = line.strip("\n")
                if len(message)>0:
                    g = Gcode({"message": message, "prot": "Eth"})
                    if self.printer.processor.is_buffered(g):
                        self.printer.commands.put(g)
                    else:
                        self.printer.unbuffered_commands.put(g)

    # Send a message		
    def send_message(self, message):
        #logging.debug("'"+message+"'")
        if message[-1] != "\n":
            message += "\n"
        try: 
            self.client.send(message)
        except socket.error, (value,message): 
            logging.error("Ethernet "+ message)
       

    # Stop receiving mesassages
    def close(self):
        self.running = False
        self.t.join()

