#!/usr/bin/env python
'''
Pipe - This uses a virtual TTY for communicating with 
Toggler or similar front end. 

Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
'''

from threading import Thread
import select
import logging
import os
import re
import subprocess

class Pipe:
    def __init__(self, printer, prot):
        self.printer = printer
        self.prot = prot

        pipe_0 = "/dev/"+self.prot+"_0"
        pipe_1 = "/dev/"+self.prot+"_1"
        p = subprocess.Popen(["tty0tty", pipe_0, pipe_1], stderr=subprocess.PIPE)
        line = p.stderr.readline()
        self.fifo = os.open(pipe_0, os.O_RDWR)
        logging.info("Pipe "+self.prot+" open. Use '"+pipe_1+"' to communicate with it")        

        self.running = True
        self.t = Thread(target=self.get_message)
        self.send_response = True
        self.t.daemon = True
        self.t.start()		


    ''' Loop that gets messages and pushes them on the queue '''
    def get_message(self):
        while self.running:
            ret = select.select( [self.fifo],[],[], 1.0 )
    	    if ret[0] == [self.fifo]:
                message = self.readline_custom()
                if len(message) > 0:        
                    self.printer.commands.put({"message": message, "prot": self.prot})            
                    logging.debug("Got message")

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
            if (cur_char == '\n' or cur_char == ""):
                return message;
            message = message + cur_char


