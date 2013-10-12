#!/usr/bin/env python
'''
A class that listens for a button press 
and sends an event if that happens.

Author: Elias Bakken
email: elias.bakken@gmail.com
Website: http://wiki.replicape.com
License: BSD

You can use and change this, but keep this heading :)
'''

from threading import Thread
import logging
from Smd import SMD

class EndStop:
    # pin is the pin where the connector is attached. 
    def __init__(self, pin, steppers, key_code, name):
        self.pin = pin
        self.steppers = steppers
        self.key_code = key_code
        self.name = name
        self.t = Thread(target=self.wait_for_event)         # Make the thread
        self.t.start()
	
    def wait_for_event(self):
        #logging.debug("Waiting for end-stop events...")
        evt_file = open("/dev/input/event1", "rb")
        while True:
            evt = evt_file.read(16) # Read the event
            evt_file.read(16)       # Discard the debounce event 
            code = ord(evt[10])            
            direction  = "down" if ord(evt[12]) else "up"
            if direction == "down" and code == self.key_code:
                for name, stepper in self.steppers.iteritems():
                    stepper.setDisabled()
                SMD.commit()           
                logging.warning("End Stop " + self.name +" hit! Disabling all steppers")



if __name__ == '__main__':
    evt_file = open("/dev/input/event1", "rb")
    while True:
        evt = evt_file.read(16) # Read the event
        evt_file.read(16)       # Discard the debounce event 
        code = ord(evt[10])
        direction  = "down" if ord(evt[12]) else "up"
        print "Switch "+str(code)+" "+direction
