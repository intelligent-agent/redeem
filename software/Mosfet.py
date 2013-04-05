#!/usr/bin/env python
'''
A Mosfet class for setting the PWM of a power mosfet for Replicape. 

Author: Elias Bakken
email: elias.bakken@gmail.com
Website: http://www.hipstercircuits.com
License: BSD

You can use and change this, but keep this heading :)
'''

DEVICE_TREE = True

if not DEVICE_TREE:
    import bbio as io

class Mosfet:

    def __init__(self, pin):
        self.pin = pin
        self.freq = 20000
        if DEVICE_TREE:
            pass
        else:    
            io.pwmEnable(pin) # Init the Pin to PWM mode
            io.pwmFrequency(pin, self.freq) # Set a frequency, not important for now
        self.setPower(0.0)
	
    '''Set duty cycle between 0 and 1'''
    def setPower(self, value):
        self.power = value
        if DEVICE_TREE:            
            with open(self.pin+"/duty", "w") as f:
                val = str(int(500000.0*value))                
                f.write(val)
        else:
            io.analogWrite(self.pin, int((1.0-value)*256.0))

    '''Set the PWM frequency'''
    def setFrequency(self, freq):
        self.freq = freq
        if DEVICE_TREE: 
            pass
        else:
            io.pwmFrequency(self.pin, freq)

    ''' return the current power level '''
    def get_power(self):
        return self.power

    def close(self):
        if DEVICE_TREE:
            pass
        else:
            io.pwmDisable(self.pin) # Init the Pin to PWM mode
		

if __name__ == "__main__":
    mosfet = Mosfet("/sys/bus/platform/devices/mosfet_ext1.12")    
    mosfet.setPower(0.5)


