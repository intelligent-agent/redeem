#!/usr/bin/env python
"""
An alarm can be executed when an error condition occurs

Author: Elias Bakken

 Redeem is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Redeem is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Redeem.  If not, see <http://www.gnu.org/licenses/>.
"""
from threading import Thread
import time
import logging

class Alarm:
    THERMISTOR_ERROR    = 0 # Thermistor error. 
    FILAMENT_JAM        = 1 # If filamet sensor is installed
    WATCHDOG_ERROR      = 2 # Can this be detected?
    ENDSTOP_HIT         = 3 # During print. 
    ALARM_TEST          = 4 # Testsignal, used during start-up

    printer = None

    def __init__(self, alarm_type, sender):
        self.type = alarm_type
        self.sender = sender
        self.printer = Alarm.printer
        
    def execute(self):
        if self.type == Alarm.THERMISTOR_ERROR: 
            self.stop_print()
            self.inform_listeners("Thermistor error! Shutting down.")
        elif self.type == Alarm.ALARM_TEST:
            logging.info("Alarm framework operational")
        else:
            logging.warning("An Alarm of unknown type was sounded!")

    # These are the different actions that can be 
    # done once an alarm is sounded. 
    def stop_print(self):
        """ Stop the print """
        self.printer.path_planner.emergency_interrupt()
        for heater in self.printer.heaters:
            heater.disable()

    def inform_listeners(self, message):
        if self.printer:
            for comm in self.printer.comms:
                comm.send_message(message) 

    def make_sound(self):
        """ Do what you are supposed to do """        
        pass

    def send_email(self):
        pass
    
    def send_sms(self):
        pass

    def record_position(self):
        pass
    
    


if __name__ == '__main__':
    alarm = Alarm(Alarm.ALARM_TEST, None)
    alarm.execute()

    #from RotaryEncoder import *
    #r = RotaryEncoder("/dev/input/event1", 360, 3)
    #f = FilamentSensor()
    #f.add_sensor(r)
    #f.set_alarm_level(1, 0)
    #time.sleep(10)
    #r.stop()
    #f.stop()



