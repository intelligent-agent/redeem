#!/usr/bin/env python
"""
Unit test suite for TemperatureSensor.py

Author: Florian Hochstrasser
email: thisis(at)parate(dot)ch
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
from mock import mock_open, patch, mock
import unittest

#Make test version- agnostic:
from sys import version_info
if version_info.major == 2:
    import __builtin__ as builtins  # pylint:disable=import-error
else:
    import builtins  # pylint:disable=import-error

from TemperatureSensor import *

class TestTemperatureSensor(unittest.TestCase):

    @classmethod
    def setUp(self):
        pin = "/sys/bus/iio/devices/iio:device0/in_voltage4_raw"
        sensor = "B57540G0104F000"
        heater_name = "5"
        self.ts = TemperatureSensor(pin, heater_name, sensor)
        self.ts.r1 = 4700
        self.ts.c1 = 0.000722378300319346
        self.ts.c2 = 0.000216301852054578
        self.ts.c3 = 9.2641025635702e-08


    def test_init_working(self):
        #If this passes, tables were loaded successfully
        self.assertEqual(self.ts.sensorIdentifier, "B57540G0104F000")

    def test_read_adc_lower_boundary(self):
        with patch.object(builtins, 'open', mock_open(read_data = "0")):
            self.assertEqual(self.ts.read_adc(), -1.0)

    def test_read_adc_upper_boundary(self):
        with patch.object(builtins, 'open', mock_open(read_data = "100000")):
            self.assertEqual(self.ts.read_adc(), -1.0)

    def test_read_adc(self):

        adc = str(4095.0/2)
        expected_voltage = 0.9002198339032731

        with patch.object(builtins, 'open', mock_open(read_data = adc)):
            self.assertTrue(abs(self.ts.read_adc() - expected_voltage) < 0.001)

    def test_voltage_to_resistance(self):

        voltage = 1.0
        expected_resistance = 5875.0

        self.assertEqual(self.ts.sensor.voltage_to_resistance(voltage), expected_resistance)

    def test_get_temperature(self):
        """With the instantiated sensor's steinhart-hart coefficients.
        resistance is 5875 ohms, corresponding to 1 V on the input pin
        """
        expected_temperature = 102.776
        with patch.object(TemperatureSensor, 'read_adc', return_value=1.0):
            self.assertTrue(abs(self.ts.get_temperature() - expected_temperature) < 0.0001)


#if __name__ == '__main__':
#    unittest.main()