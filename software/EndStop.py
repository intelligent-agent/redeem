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

class EndStop:
    # pin is the pin where the connector is attached. 
    def __init__(self, pin):
        self.pin = pin
	
    def wait_for_event(self):
        evt_file = open("/dev/input/event1", "rb")
        while True:
            evt = evt_file.read(16) # Read the event
            evt_file.read(16)       # Discard the debounce event 
            code = ord(evt[10])
            direction  = "down" if ord(evt[12]) else "up"
            print "Switch "+str(code)+" "+direction


if __name__ == '__main__':
    evt_file = open("/dev/input/event5", "rb")
    while True:
        evt = evt_file.read(16) # Read the event
        evt_file.read(16)       # Discard the debounce event 
        code = ord(evt[10])
        direction  = "down" if ord(evt[12]) else "up"
        print "Switch "+str(code)+" "+direction
