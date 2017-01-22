#!/usr/bin/env python
"""
The watchdog on BBB simply opens a file and holds the FD until it shuts down.
If something goes wrong with the BBB or redeem, the watchdog will kick in in
one minute.


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


class Watchdog:

    def __init__(self, path="/dev/watchdog", refresh=30):
        self.path = path
        self.refresh = refresh
        self.t = Thread(target=self._run, name="Watchdog")
        self.running = False

        self.nowayout = 1

        with open("/proc/cmdline", "r") as f:
            cmdline = f.readline()
            if "omap_wdt.nowayout=0" in cmdline:
                self.nowayout = 0

    def start(self):
        if self.nowayout:
            logging.warning(("Watchdog has 'nowayout' enabled. "
                             "Stopping redeem would cause a system reset."
                             "Please add 'omap_wdt.nowayout=0' to the kernel "
                             "command line in order to enable the watchdog."
                             "Watchdog is not enabled."))
            return
        self.time_left = self.refresh
        self.running = True
        self.fd = open(self.path, "w")
        self.t.start()
        logging.info("Watchdog started, refresh {} s".format(
            self.refresh))

    def stop(self):
        if self.nowayout or not self.running:
            return
        self.time_left = 0
        self.running = False
        self.t.join()
        self.fd.write("V")
        self.fd.close()
        logging.debug("Watchdog stopped")

    def _run(self):
        """ While more time on the clock,
        stay in the inner loop. If not, carry out the
        timeout function """
        while self.running:
            while self.time_left and self.running:
                time.sleep(1)
                self.time_left -= 1
            self.poke_watchdog()
            self.time_left = self.refresh

    def poke_watchdog(self):
        """ Write something to the watchdog file. """
        logging.debug("Poking watchdog")
        self.fd.write("\n")
        self.fd.flush()


if __name__ == '__main__':
    logformat = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
    logdateformat = '%m-%d %H:%M'

    logging.basicConfig(level=logging.DEBUG,
                        format=logformat,
                        datefmt=logdateformat)
    wd = Watchdog(refresh=1)
    wd.start()
    time.sleep(10)
    wd.stop()
