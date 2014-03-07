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
from Stepper import Stepper

class EndStop:

    callback = None                 # Override this to get events
    inputdev = "/dev/input/event0"  # File to listen to events

    def __init__(self, key_code, name, invert=False):
        self.key_code = key_code
        self.name = name
        self.invert = invert
        self.t = Thread(target=self._wait_for_event)
        self.t.daemon = True
        self.t.start()
	
    def _wait_for_event(self):
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
