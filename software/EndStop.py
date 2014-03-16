#!/usr/bin/env python
'''
A class that listens for a button press 
and sends an event if that happens.

Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
'''

from threading import Thread
import logging
import mmap
import struct
import re
from Stepper import Stepper

class EndStop:

    callback = None                 # Override this to get events
    inputdev = "/dev/input/event0"  # File to listen to events

    def __init__(self, pin, key_code, name, invert=False):
        self.pin = pin
        self.key_code = key_code
        self.name = name
        self.invert = invert
        self.t = Thread(target=self._wait_for_event)
        self.t.daemon = True
        self.hit = False
        self.t.start()
	   
    def get_gpio_bank_and_pin(self):
        matches=re.compile('GPIO([0-9])_([0-9]+)').search(self.pin)
        tup =  matches.group(1,2)
        tup = (int(tup[0]), int(tup[1]))
        return tup

    def get_pin(self):
        return self.pin

    def _wait_for_event(self):
        evt_file = open(EndStop.inputdev, "rb")
        while True:
            evt = evt_file.read(16) # Read the event
            evt_file.read(16)       # Discard the debounce event (or whatever)
            code = ord(evt[10])            
            direction  = "down" if ord(evt[12]) else "up"
            if code == self.key_code:
                if self.invert == True and direction == "down":
                    self.hit = True 
                    if EndStop.callback != None:
                        EndStop.callback(self)
                elif self.invert == False and direction == "up":
                    self.hit = True
                    if EndStop.callback != None:
                        EndStop.callback(self)
                else:
                    self.hit = False

    ''' Read the current ensdstop value from GPIO using PRU1 '''
    def read_value(self):
        PRU_ICSS = 0x4A300000 
        PRU_ICSS_LEN = 512*1024
        RAM2_START = 0x00012000

        with open("/dev/mem", "r+b") as f:	       
            ddr_mem = mmap.mmap(f.fileno(), PRU_ICSS_LEN, offset=PRU_ICSS) 
            state = struct.unpack('LLL', ddr_mem[RAM2_START:RAM2_START+12])
            if self.name == "X1":
                self.hit = bool(state[0] & (1<<0))
            elif self.name == "Y1":
                self.hit = bool(state[0] & (1<<1))
            elif self.name == "Z1":
                self.hit = bool(state[0] & (1<<2))
            elif self.name == "X2":
                self.hit = bool(state[0] & (1<<3))
            elif self.name == "Y2":
                self.hit = bool(state[0] & (1<<4))
            elif self.name == "Z2":
                self.hit = bool(state[0] & (1<<5))
            else:
                raise RuntimeError('Invalid endstop name')
        return self.hit


