#!/usr/bin/env python
"""
This file is for adding support to rotary encoders, 
for more information see Wikipedia: 
https://en.wikipedia.org/wiki/Rotary_encoder

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
from evdev import InputDevice, ecodes
from threading import Thread
import time
import math
import logging


class RotaryEncoder:
    def __init__(self, dev, cpr, d):
        self.dev = InputDevice(dev)
        self.cpr = float(cpr) # Cycles pr revolution
        self.d = d
        self.distance = 0
        self.step = 0
        self.t = Thread(target=self._wait_for_event, name="RotaryEncoder")
        self.running = True
        self.t.start()

    def get_distance(self):
        return self.distance

    def stop(self):
        self.running = False
        self.t.join()

    def _wait_for_event(self):
        for event in self.dev.read_loop():
            if event.type == ecodes.EV_REL:
                self.step += event.value
                self.rounds = self.step/self.cpr
                self.distance = self.rounds*math.pi*self.d if self.rounds != 0 else 0
            if not self.running:
                break

if __name__ == '__main__':
    r = RotaryEncoder("/dev/input/event1", 360, 3)
    time.sleep(10)
    r.stop()
