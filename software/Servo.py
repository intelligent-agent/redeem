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

from Fan import Fan
from threading import Thread
import time
import math
import Queue
from multiprocessing import JoinableQueue
import logging

class Servo(Fan):
    def __init__(self, channel, pulse_width_start, pulse_width_stop, init_angle, turnoff_timeout=0):
        """Define a new software controllable servo with adjustable speed control

        Keyword arguments:
        pulse_width_start -- The minimum pulse width defining the lowest angle
        pulse_width_stop -- The maximum pulse width defining the biggest angle
        init_angle -- Initial angle that the servo should take when it is powered on. Range is 0 to 180deg
        turnoff_timeout -- number of seconds after which the servo is turned off if no command is received. 0 = never turns off
        """

        super(Servo, self).__init__(channel)

        self.pulse_width_start = pulse_width_start
        self.pulse_width_stop = pulse_width_stop
        self.turnoff_timeout = turnoff_timeout

        self.current_pulse_width = int(init_angle*(self.pulse_width_stop-self.pulse_width_start)/180.0+self.pulse_width_start)
        self.last_pulse_width = self.current_pulse_width

        self.queue = JoinableQueue(1000)
        self.lastCommandTime = 0

        self.t = Thread(target=self._wait_for_event)
        self.t.daemon = True
        self.running = True
        self.t.start()

    def set_angle(self,angle, speed = 60, asynchronous = True):
        ''' Set the servo angle to the given value, in degree, with the given speed in deg / sec '''
        pulse_width = int(angle*(self.pulse_width_stop-self.pulse_width_start)/180.0+self.pulse_width_start)
        last_angle = int((self.last_pulse_width-self.pulse_width_start)/float(self.pulse_width_stop-self.pulse_width_start)*180.0)

        t = (math.fabs(angle-last_angle)/speed) / math.fabs(angle-last_angle)

        for w in xrange(self.last_pulse_width, pulse_width, 1 if pulse_width>=self.last_pulse_width else -1):
            self.queue.put((w,t))

        self.last_pulse_width = pulse_width
        
        if not asynchronous:
            self.queue.join()

    def turn_off(self):
        self.set_value(0)

    def _wait_for_event(self):
        try:
            while self.running:
                try:
                    ev = self.queue.get(block=True, timeout=1)
                except Queue.Empty:
                    if self.turnoff_timeout>0 and self.lastCommandTime>0 and time.time()-self.lastCommandTime>self.turnoff_timeout:
                        self.lastCommandTime = 0
                        self.turn_off()
                    continue

                self.current_pulse_width = ev[0]
                self.set_value(self.current_pulse_width/4095.0)
                self.lastCommandTime = time.time()
                time.sleep(ev[1])

                self.queue.task_done()

        except Exception:
            logging.exception("Exception in loop: ")


if __name__ == '__main__':
    import os

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M')

   
    fan = Servo(1,500,750,90) 

    Servo.set_PWM_frequency(100)
    while True:
        try:
            f=int(raw_input('Input:'))
            fan.set_angle(f)
        except ValueError:
            print "Not a number"
        except KeyboardInterrupt:
            fan.turn_off()
            print ""
            break


