#!/usr/bin/env python
"""
A watchdog with a timer and a reset switch that will disable 
the steppers if it is not poked within a predefined time. 

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
from threading import Thread, Lock
import time
import logging
from six import iteritems

class StepperWatchdog:

    def __init__(self, printer, timeout=60):
        self.printer = printer
        self.timeout = timeout
        self.time_left = 0
        self.lock = Lock()
        self.t = Thread(target=self._run, name="StepperWatchdog")
        self.running = False

    def start(self):
        self.running = True
        self.t.start()
        logging.info("Stepper watchdog started, timeout {} s".format(
            self.timeout))

    def stop(self):
        if self.running:
            logging.debug("Stopping stepper watchdog")
            self.lock.acquire()
            self.time_left = 0
            self.lock.release()
            self.running = False
            self.t.join()
        else:
            logging.debug("Attempted to stop StepperWatchdog when it is not running")

    def reset(self):
        self.lock.acquire()
        self.time_left = self.timeout
        self.lock.release()

    def _run(self):
        """ While more time on the clock, 
        stay in the inner loop. If not, carry out the 
        timeout function """
        while self.running:
            if self.time_left:
                while self.time_left and self.running:
                    time.sleep(1)
                    self.lock.acquire()
                    self.time_left -= 1
                    self.lock.release()
                self._on_timeout()
            else:      
                time.sleep(1)

    def _on_timeout(self):
        """ Run this when timeout occurs. """
        logging.debug("Stepper watchdog timeout")
        if not self.printer:
            return
        for name, stepper in iteritems(self.printer.steppers):
            if stepper.in_use and stepper.enabled:
                # Stepper should be enabled, but is not.
                stepper.set_disabled(True)  # Force update

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')
    swd = StepperWatchdog(None, 3)
    swd.start()
    swd.reset()
    time.sleep(4)
    swd.stop()

