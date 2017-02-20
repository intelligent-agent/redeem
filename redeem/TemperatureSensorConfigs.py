#!/usr/bin/env python
"""
Steinhart-Hart coefficients derived from temperature <-> resistance tables.
Suggested temperature values for calculation of the coefficients:
25, 150 and 250 C

Use one of the following scripts to calcuate the coefficients:
- http://www.thinksrs.com/downloads/programs/Therm%20Calc/NTCCalibrator/NTCcalculator.htm
- https://github.com/MarlinFirmware/Marlin/blob/Development/Marlin/scripts/createTemperatureLookupMarlin.py

Derived in part from smoothieware.
Source: https://github.com/Smoothieware/Smoothieware.

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

thermistors_shh = [
    # name, r,
    # c1, c2, c3
    # EPCOS100K with b= 4066K
    ["B57540G0104F000", 4700,
     0.000722378300319346, 0.000216301852054578, 9.2641025635702e-08],
    # EPCOS100K with b = 4092K, may be incorrect.
    ["B57560G1104F", 4700,
     0.7221363090e-3, 2.167665665e-4, 0.8929358045e-07],
    # EPCOS100K with b = 4092K (Hexagon)
    ["B57560G104F", 4700,
     0.7273235045e-3, 2.154664008e-4, 0.9570344827e-07],
    # EPCOS10K, these values might be incorrect.
    ["B57561G0103F000", 4700,
     0.008598824746, 0.0002593587338, 1.348387402e-07],
    # Vishay100K
    ["NTCS0603E3104FXT", 4700,
     0.0007022607370, 0.0002209155484, 7.101626461e-08],
    # Honeywell100K
    ["135-104LAG-J01", 4700,
     0.000596153185928425, 0.000231333192738335, 6.19534004306738e-08],
    # Semitec (E3D V6)
    ["SEMITEC-104GT-2", 4700,
     0.000811290160145459, 0.000211355789144265, 7.17614730463848e-08],
    # DYZE hightemp thermistor, may be incorrect.
    ["DYZE", 4700,
     0.004628116888, 0.0001812508833, 3.185110657e-06],
    # RobotDigg.com's 3950-100K thermistor (part number HT100K3950-1)
    ["HT100K3950", 4700,
     0.7413760971e-3, 2.117947876e-4, 1.141950936e-7],
    # Semitec 104NT-4-R025H42G Thermistor
    ["Semitec-104NT4", 4700,
     0.797110609710217e-3, 2.13433144381270e-4, 0.65338987554e-7],
]


"""
Configuration for PT100 sensors. The coefficients fit in the following formula:
The coefficients are general use and represent platinum resistance sensors
according to the ITS-90

r = r0 * (1 + a*t + b*t^2) for the range 0 deg C ... 850 deg C
r0 is the reference resistance at 0 deg C

Temperature (> 0 deg C)
t = -r0*a + (r0^2*a^2 - 4*r0*b * (r0-r))^(1/2) / 2*r0*b
"""

pt100 = [
    # identifier,               pullup, r0,     a,          b
    ["E3D-PT100-AMPLIFIER", 4700, 100, 0.0039083, -5.77e-07],
    ["PT100-GENERIC-PLATINUM", 4700, 100, 0.0039083, -5.77e-07]
]

""" Configuration for thermocouple boards having linear v/deg scale"""
tboard = [
    ["Tboard", 0.005],
]
