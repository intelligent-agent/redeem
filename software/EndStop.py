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
        self.hit = False
        self.t.start()
	   
    def set_path_planner(self,planner):
        self.path_planner=planner

    def get_gpio_bank_and_pin(self):
        matches=re.compile('GPIO([0-9])_([0-9]+)').search(self.pin)
        tup =  matches.group(1,2)
        tup = (int(tup[0]), int(tup[1]))
        return tup

    def set_initial_value_from_gpio(self,v):
        self.hit=True if (v==1 and not self.invert) or (v==0 and self.invert) else False
        logging.debug("Endstop "+self.name+": "+("hit" if self.hit else "not hit"))

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
