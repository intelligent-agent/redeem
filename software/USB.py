#!/usr/bin/env python
'''
USB communication file for Replicape. 

Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
'''

from threading import Thread
import select
import logging

class USB:
    def __init__(self, printer):
        self.printer = printer
        self.tty = open("/dev/ttyGS0", "r+")
        self.running = True
        self.debug = 0
        self.t = Thread(target=self.get_message)
        self.t.daemon = True
        self.t.start()		

    # Loop that gets messages and pushes them on the queue
    def get_message(self):
        while self.running:
            ret = select.select( [self.tty],[],[], 1.0 )
    	    if ret[0] == [self.tty]:
                message = self.tty.readline().strip("\n")
                if len(message) > 0:  
                    self.printer.commands.put({"message": message, "prot": "USB"})
                

    # Send a message		
    def send_message(self, message):
        if message[-1] != "\n":
            message += "\n"
        self.tty.write(message)

    # Stop receiving mesassages
    def close(self):
        self.running = False
        self.t.join()

