#!/usr/bin/env python
'''
Ethernet communication file for Replicape. 

Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
'''

from threading import Thread
import socket
import logging
import select

size = 1024 

class Ethernet:
    def __init__(self, queue):
        self.queue = queue
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
        print "Ethernet bound to port "+str(port)
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
                    chunk = self.client.recv(1)
                    if chunk == '':
                        logging.warning("Ethernet: Connection reset by Per.")
                        self.client.close()             
                        break
                    line = line + chunk
                if not "\n" in line: # Make sure the whole line was read. 
                    break
                message = line.strip("\n")

                self.queue.put({"message": message, "prot": "Eth"})

    # Send a message		
    def send_message(self, message):
        #logging.debug("'"+message+"'")
        if message[-1] != "\n":
            message += "\n"
        self.client.send(message)

    # Stop receiving mesassages
    def close(self):
        self.running = False
        self.t.join()

