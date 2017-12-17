#!/usr/bin/env python
"""
Enable heaters with a pin. 

Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
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

class Enable:

    def __init__(self, pin, inverted=True):
        self.pin = pin
        self.inverted = inverted

    def set_enabled(self):
        with open("/sys/class/gpio/{}/value".format(self.pin), "w") as f:
            f.write("{}\n".format(int(not self.inverted)))

    def set_disabled(self):
        with open("/sys/class/gpio/{}/value".format(self.pin), "w") as f:
            f.write("{}\n".format(int(self.inverted)))



if __name__ == '__main__':
    en = Enable("gpio18")
    en.set_enabled()
    en.set_disabled()


