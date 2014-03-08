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

    def _wait_for_event(self):
        #logging.debug("Waiting for end-stop events...")
        evt_file = open(EndStop.inputdev, "rb")
        while True:
            evt = evt_file.read(16) # Read the event
            evt_file.read(16)       # Discard the debounce event (or whatever)
            code = ord(evt[10])            
            direction  = "down" if ord(evt[12]) else "up"
            if code == self.key_code and EndStop.callback != None:
                if self.invert == False and direction == "down":
                    EndStop.callback(self)
                elif self.invert == True and direction == "up":
                    EndStop.callback(self)

if __name__ == '__main__':
    evt_file = open("/dev/input/event1", "rb")
    while True:
        evt = evt_file.read(16) # Read the event
        evt_file.read(16)       # Discard the debounce event 
        code = ord(evt[10])
        direction  = "down" if ord(evt[12]) else "up"
        print "Switch "+str(code)+" "+direction
