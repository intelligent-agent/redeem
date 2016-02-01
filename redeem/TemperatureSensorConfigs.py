#!/usr/bin/env python
"""
Steinhart-Hart coefficients derived from temperature <-> resistance tables.
Suggested temperature values for calculation of the coefficients: 25, 150 and 250 C
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
    #name,                  r2,   c1,                    c2,                    c3
    ["B57540G0104F000",     4700, 0.007229943855,        0.0002161977696,       9.302254945e-08],  # EPCOS100K with b= 4066K
    ["B57560G1104F",        4700, 0.007221363090,        0.0002167665665,       8.929358045e-08], #EPCOS100K with b = 4092K
    ["B57561G0103F000",     4700, 0.008598824746,        0.0002593587338,       1.348387402e-07], #EPCOS10K
    ["135-104LAG-J01",      4700, 0.000596153185928425,  0.000231333192738335,  6.19534004306738e-08], # Honeywell100K
    ["104GT-2",             4700, 0.0008110813304,       0.0002113914932,       7.163159867e-06], # Semitec
    ["DYZE",                4700, 0.004628116888,        0.0001812508833,       3.185110657e-06] #DYZE hightemp thermistor
]


"""
A list of beta values for various thermistors. Acquired in datasheets from
the suppliers. r2 is the pullup, r1 another resistor. r0 and t0 are the
thermistors resistance / temperature pair at room temperature. Could be used
if Steinhart-Hart coefficients cannot be determined for a specific sensor.
"""

thermistors_beta = [
    # name,                 r1,  r2,   beta,    r0,        t0
    ["B57540G0104F000",     0,   4700, 4066,    100000,    25], #EPCOS100K
    ["B57560G1104F",        0,   4700, 4092,    100000,    25], #EPCOS100K
    ["B57561G0103F000",     0,   4700, 3450,    10000,     25], #EPCOS10K
    ["135-104LAG-J01",      0,   4700, 3974,    100000,    25], #Honeywell100K / QU-BD
    ["104GT-2",             0,   4700, 4267,    100000,    25], #Semitec
    ["DYZE",                0,   4700, 5081.32, 4500000,   25]  #DYZE hightemp thermistor
]


"""
Configuration for PT100 sensors. The coefficients fit in the following formula:
The coefficients are general use and represent platinum resistance sensors according
to the ITS-90

r = r0 * (1 + a*t + b*t^2) for the range 0 deg C ... 850 deg C
r0 is the reference resistance at 0 deg C

Temperature (> 0 deg C)
t = -r0*a + (r0^2*a^2 - 4*r0*b * (r0-r))^(1/2) / 2*r0*b
"""

pt100 = [
    #identifier,            r0,     a,          b
    ["E3D-PT100-AMPLIFIER", 100,    0.0039083, -5.77e-07],
    ["PT100-GENERIC-PLATINUM", 100,    0.0039083, -5.77e-07]
]