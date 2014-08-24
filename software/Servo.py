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

class ServoCommand(object):
    def __init__(self, pulse_width, wait_time):
        self.pulse_width = pulse_width
        self.wait_time = wait_time


class Servo(Fan):
    def __init__(self, channel, pulse_width_start, pulse_width_stop, init_angle):
        """ Channel is the channel that the fan is on (0-7) """
        super(Servo, self).__init__(channel)

        self.pulse_width_start = pulse_width_start
        self.pulse_width_stop = pulse_width_stop

        self.current_pulse_width = int(init_angle*(self.pulse_width_stop-self.pulse_width_start)/180.0+self.pulse_width_start)
        self.last_pulse_width = self.current_pulse_width

        self.queue = JoinableQueue(1000)

        self.t = Thread(target=self._wait_for_event)
        self.t.daemon = True
        self.running = True
        self.t.start()

    def set_angle(self,angle, speed = 50):
        ''' Set the servo angle to the given value, in degree, with the given speed in deg / sec '''
        pulse_width = int(angle*(self.pulse_width_stop-self.pulse_width_start)/180.0+self.pulse_width_start)
        last_angle = int((self.last_pulse_width-self.pulse_width_start)/float(self.pulse_width_stop-self.pulse_width_start)*180.0)

        t = (math.fabs(angle-last_angle)/speed) / math.fabs(angle-last_angle)

        for w in xrange(self.last_pulse_width, pulse_width, 1 if pulse_width>=self.last_pulse_width else -1):
            self.queue.put(ServoCommand(w,t))

        self.last_pulse_width = pulse_width

    def turn_off(self):
        self.set_value(0)

    def _wait_for_event(self):
        try:
            while self.running:
                try:
                    ev = self.queue.get(block=True, timeout=1)
                except Queue.Empty:
                    continue

                self.current_pulse_width = ev.pulse_width
                self.set_value(self.current_pulse_width/4095.0)
                time.sleep(ev.wait_time)

                self.queue.task_done()

        except Exception:
            logging.exception("Exception in loop: ")


if __name__ == '__main__':
    import numpy as np
    import os
    import logging

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


