#!/usr/bin/env python
"""
A servo is for switching some tools on/off. This one is for Replicape.

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: GNU GPL v3: http://www.gnu.org/copyleft/gpl.html

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
from builtins import range
import time
import math
import Queue
from multiprocessing import JoinableQueue
import logging
from PWM_pin import PWM_pin
from ShiftRegister import ShiftRegister

class Servo:
    def __init__(self, channel, pulse_width_min, pulse_width_max, angle_min, angle_max, init_angle, turnoff_timeout=0):
        """Define a new software controllable servo with adjustable speed control

        Keyword arguments:
        pulse_width_min -- The minimum pulse width defining the lowest angle
        pulse_width_max -- The maximum pulse width defining the biggest angle
        init_angle -- Initial angle that the servo should take when it is powered on. Range is 0 to 180deg
        turnoff_timeout -- number of seconds after which the servo is turned off if no command is received. 0 = never turns off
        """

        self.angle_min = angle_min
        self.angle_max = angle_max
        self.angle_total = angle_max-angle_min
        self.pulse_width_min = pulse_width_min
        self.pulse_width_max = pulse_width_max
        self.pulse_width_total = pulse_width_max-pulse_width_min
        
        self.turnoff_timeout = turnoff_timeout

        self.current_pulse_width = self.angle_to_pulse_width(init_angle)
        self.last_pulse_width = self.current_pulse_width

        self.last_angle = init_angle

        self.pulse_length = 20.0*10.0**-3.0 # 20 ms

        logging.debug("Angle min: {} deg".format(self.angle_min))
        logging.debug("Angle max: {} deg".format(self.angle_max))
        logging.debug("Angle tot: {} deg".format(self.angle_total))
        logging.debug("Pulse min: {} ms".format(self.pulse_width_min*1000.0))
        logging.debug("Pulse max: {} ms".format(self.pulse_width_max*1000.0))
        logging.debug("Pulse tot: {} ms".format(self.pulse_width_total*1000.0))

        self.queue = JoinableQueue(1000)
        self.lastCommandTime = 0

        self.t = Thread(target=self._wait_for_event, name="Servo")
        self.t.daemon = True
        self.running = True
        self.t.start()

        # Branch based on channel type.

        if type(channel) == int: # Revision A
            self.pwm = PWM(channel, 50, self.current_pulse_width)
        else: # Revision B
            # Set up the Shift register for enabling this servo
            if channel == "P9_14":
                shiftreg_nr = 1
                self.pwm = PWM_pin(channel, 50, self.current_pulse_width)
            elif channel == "P9_16":
                shiftreg_nr = 2
                self.pwm = PWM_pin(channel, 50, self.current_pulse_width)
            else:
                logging.warning("Tried to assign servo to an unknown channel/pin: "+str(channel))
                return        

            ShiftRegister.make(5)
            self.shift_reg = ShiftRegister.registers[shiftreg_nr]
        self.set_enabled()
        self.pwm.set_value(self.angle_to_pulse_width(init_angle)/self.pulse_length)

    def set_enabled(self, is_enabled=True):
        if is_enabled:
            self.shift_reg.add_state(0x01)
        else:
            self.shift_reg.remove_state(0x01)


    def set_angle(self, angle, speed=60, asynchronous=True):
        ''' Set the servo angle to the given value, in degree, with the given speed in deg / sec '''
        angle = max(min(self.angle_max, angle), self.angle_min)
        pulse_width = self.angle_to_pulse_width(angle)
        last_angle = self.last_angle

        logging.debug("Updating angle from {} (pw={}) to {} (pw={}) ".format(last_angle, self.last_pulse_width, angle, pulse_width))

        if angle == last_angle:
            return
        
        t = (math.fabs(angle-last_angle)/speed) / math.fabs(angle-last_angle)

        

        if angle>=last_angle:
            for a in range(int(last_angle), int(angle+1), 1):
                self.queue.put((self.angle_to_pulse_width(a),t))
        else:
            for a in range(int(last_angle), int(angle-1), -1):
                self.queue.put((self.angle_to_pulse_width(a),t))
        
        self.last_pulse_width = pulse_width
        self.last_angle = angle
        
        if not asynchronous:
            self.queue.join()

    def turn_off(self):
        self.pwm.set_enabled(False)

    def stop(self):
        self.running = False
        self.t.join()
        self.turn_off()

    def _wait_for_event(self):
        while self.running:
            try:
                ev = self.queue.get(block=True, timeout=1)
            except Queue.Empty:
                if self.turnoff_timeout>0 and self.lastCommandTime>0 and time.time()-self.lastCommandTime>self.turnoff_timeout:
                    self.lastCommandTime = 0
                    self.turn_off()
                continue
            except Exception:
                # To avoid exception printed on output
                pass

            self.current_pulse_width = ev[0]
            #logging.debug("setting pulse width to "+str(self.current_pulse_width))
            self.pwm.set_value(self.current_pulse_width/self.pulse_length)
            self.lastCommandTime = time.time()
            time.sleep(ev[1])

            self.queue.task_done()


    def angle_to_pulse_width(self, angle):
        return ((angle-self.angle_min)/self.angle_total)*self.pulse_width_total + self.pulse_width_min

    def pulse_width_to_angle(self, pulse_width):
        return (((pulse_width-self.pulse_width_min)/(self.pulse_width_total))*self.angle_total)+self.angle_min
    
if __name__ == '__main__':
   
    servo_0 = Servo("P9_14", 0.1, 0.2, 90) 
    servo_1 = Servo("P9_16", 0.1, 0.2, 90) 

    while True:
        for i in range(1, 180):
            servo_0.set_angle(i)
            servo_1.set_angle(i)
        for i in range(180, 1, -1):
            servo_0.set_angle(i)
            servo_1.set_angle(i)


