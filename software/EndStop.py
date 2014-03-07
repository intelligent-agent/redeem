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
import re

class EndStop:
    # pin is the pin where the connector is attached. 
    def __init__(self, pin, key_code, name):
        self.pin = pin
        self.key_code = key_code
        self.name = name
        self.t = Thread(target=self.wait_for_event)         # Make the thread
        self.t.daemon = True
        self.path_planner = None
        self.hit = True
        self.t.start()
	   
    def setInitialValue(self,v):
        self.hit=v

    def set_path_planner(self,planner):
        self.path_planner=planner

    def isHit(self):
        return self.hit

    def get_gpio_bank_and_pin(self):
        matches=re.compile('GPIO([0-9])_([0-9]+)').search(self.pin)
        tup =  matches.group(1,2)

        tup = (int(tup[0]), int(tup[1]))

        return tup

    def get_pin(self):
        return self.pin

    def wait_for_event(self):
        #logging.debug("Waiting for end-stop events...")
        evt_file = open("/dev/input/event0", "rb")
        while True:
            evt = evt_file.read(16) # Read the event
            evt_file.read(16)       # Discard the debounce event 
            code = ord(evt[10])            
            direction  = "down" if ord(evt[12]) else "up"
            if direction == "up" and code == self.key_code:
                self.hit = True          
                #if self.path_planner != None: self.path_planner.interrupt_move();
                logging.warning("End Stop " + self.name +" hit! Disabling all steppers")
            elif direction == "down" and code == self.key_code:
                self.hit = False  


if __name__ == '__main__':
    evt_file = open("/dev/input/event1", "rb")
    while True:
        evt = evt_file.read(16) # Read the event
        evt_file.read(16)       # Discard the debounce event 
        code = ord(evt[10])
        direction  = "down" if ord(evt[12]) else "up"
        print "Switch "+str(code)+" "+direction
