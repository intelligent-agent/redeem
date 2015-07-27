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
import time
import math
import Queue
from multiprocessing import JoinableQueue
import logging
from PWM_pin import PWM_pin
from ShiftRegister import ShiftRegister

class Servo:
    def __init__(self, channel, pulse_width_start, pulse_width_stop, init_angle, turnoff_timeout=0):
        """Define a new software controllable servo with adjustable speed control

        Keyword arguments:
        pulse_width_start -- The minimum pulse width defining the lowest angle
        pulse_width_stop -- The maximum pulse width defining the biggest angle
        init_angle -- Initial angle that the servo should take when it is powered on. Range is 0 to 180deg
        turnoff_timeout -- number of seconds after which the servo is turned off if no command is received. 0 = never turns off
        """

        self.pulse_width_start = pulse_width_start
        self.pulse_width_stop = pulse_width_stop
        self.turnoff_timeout = turnoff_timeout

        self.current_pulse_width = init_angle*(self.pulse_width_stop-self.pulse_width_start)/180.0+self.pulse_width_start
        self.last_pulse_width = self.current_pulse_width

        self.queue = JoinableQueue(1000)
        self.lastCommandTime = 0

        self.t = Thread(target=self._wait_for_event)
        self.t.daemon = True
        self.running = True
        self.t.start()

        self.pwm = PWM_pin(channel, 100, self.current_pulse_width)

        # Set up the Shift register for enabling this servo
        if channel == "P9_14":
            shiftreg_nr = 3
        elif channel == "P9_16":
            shiftreg_nr = 2
        else:
            logging.warning("Tried to assign servo to an unknown channel/pin: "+str(channel))
            return

        ShiftRegister.make()
        self.shift_reg = ShiftRegister.registers[shiftreg_nr]
        self.set_enabled()

    def set_enabled(self, is_enabled=True):
        if is_enabled:
            self.shift_reg.add_state(0x01)
        else:
            self.shift_reg.remove_state(0x01)


    def set_angle(self, angle, speed=60, asynchronous=True):
        ''' Set the servo angle to the given value, in degree, with the given speed in deg / sec '''
        pulse_width = angle*(self.pulse_width_stop-self.pulse_width_start)/180.0+self.pulse_width_start
        last_angle = (self.last_pulse_width-self.pulse_width_start)/float(self.pulse_width_stop-self.pulse_width_start)*180.0
        
        
        t = (math.fabs(angle-last_angle)/speed) / math.fabs(angle-last_angle)

        for w in xrange(int(self.last_pulse_width*1000), int(pulse_width*1000), (1 if pulse_width>=self.last_pulse_width else -1)):
            self.queue.put((w/1000.0,t))

        self.last_pulse_width = pulse_width
        
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
            self.pwm.set_value(self.current_pulse_width)
            self.lastCommandTime = time.time()
            time.sleep(ev[1])

            self.queue.task_done()


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


