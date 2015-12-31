#!/usr/bin/env python
"""
Steinhart-Hart coefficients derived from temperature <-> resistance tables.
Suggested temperature values for calculation of the coefficients: 25°, 150° and 250° C
Use one of the following scripts to calcuate the coefficients:
- http://www.thinksrs.com/downloads/programs/Therm%20Calc/NTCCalibrator/NTCcalculator.htm
- https://github.com/MarlinFirmware/Marlin/blob/Development/Marlin/scripts/createTemperatureLookupMarlin.py

Derived from smoothieware's thermistor tables.
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

thermistors_steinharthart_coefficients[
	#name,            		r1,  r2,   c1,                    c2,                     c3	
	["B57540G0104F000",       0,   4700, 0.007229943855, 0.0002161977696,  9.302254945e-08],  # EPCOS100K
	["B57560G1104F", 		0, 	 4700, 0.007221363090,	0.0002167665665,	   8.929358045e-08], #EPCOS100K
	["B57561G0103F000",		0,	 4700, 0.008598824746,	0.0002593587338,	   1.348387402e-07], #EPCOS10K
    ["135-104LAG-J01",   0,   4700, 0.000596153185928425, 0.000231333192738335,  6.19534004306738e-08], # Honeywell100K
    ["104GT-2",         0,   4700, 0.0008110813304, 0.0002113914932,  7.163159867e-06], # Semitec
]AA