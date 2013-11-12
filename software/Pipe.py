#!/usr/bin/env python
'''
Pipe communication file for Replicape. 

Author: Elias Bakken
email: elias.bakken@gmail.com
Website: http://www.hipstercircuits.com
License: BSD

You can use and change this, but keep this heading :)
'''

from threading import Thread
import select
import logging
import os, tempfile
import re


with open("/var/log/tty0tty.log", 'r') as f:
    for line in f:
		pass

m = re.search('\(.*\) ', line)
filename = m.group(0)[1:-2]

class Pipe:
    def __init__(self, queue):
        self.queue = queue
        self.running = True
        self.debug = 0
        self.fifo = os.open(filename, os.O_RDWR)
        self.t = Thread(target=self.get_message)
        self.t.daemon = True
        self.t.start()		

    # Loop that gets messages and pushes them on the queue
    def get_message(self):
        while self.running:
            ret = select.select( [self.fifo],[],[], 1.0 )
    	    if ret[0] == [self.fifo]:
                #message = os.read(self.fifo, 100).strip("\n")  
                message = readline_custom(self.fifo)
                if len(message) > 0:        
                    #logging.debug("Message: "+message+" ("+message.encode("hex")+")")
                    self.queue.put({"message": message, "prot": "PIPE"})            

    # Send a message		
    def send_message(self, message):
        #logging.debug("FIFO: writing '"+message+"'")
        if message[-1] != "\n":
            message += "\n"
            os.write(self.fifo, message)
        #logging.debug("FIFO: written")

    # Stop receiving mesassages
    def close(self):
        self.running = False
        self.t.join()
        self.fifo.close()


def tail( f, window=20 ):
    BUFSIZ = 1024
    f.seek(0, 2)
    bytes = f.tell()
    size = window
    block = -1
    data = []
    while size > 0 and bytes > 0:
        if (bytes - BUFSIZ > 0):
            # Seek back one whole BUFSIZ
            f.seek(block*BUFSIZ, 2)
            # read BUFFER
            data.append(f.read(BUFSIZ))
        else:
            # file too small, start from begining
            f.seek(0,0)
            # only read what was not read
            data.append(f.read(bytes))
        linesFound = data[-1].count('\n')
        size -= linesFound
        bytes -= BUFSIZ
        block -= 1
    return '\n'.join(''.join(data).splitlines()[-window:])


def readline_custom(fifo):
    message = ""

    while True:
        cur_char = os.read(fifo, 1)

        #Check for newline char    
        if (cur_char == '\n' or cur_char == ""):
            return message;
   
        #Add character to message
        message = message + cur_char


