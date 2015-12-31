#!/usr/bin/env python
"""
A list of beta values for various thermistors. Acquired in datasheets from
the suppliers. r2 is the pullup, r1 another resistor. r0 and t0 are the
thermistors resistance / temperature pair at room temperature.

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

thermistors_beta[
	# name,            		r1,  r2,   beta,    r0,        t0
	["B57540G0104F000", 	0,   4700, 4066,    100000,    25], #EPCOS100K
	["B57560G1104F", 		0, 	 4700, 4092,	100000,	   25], #EPCOS100K
	["B57561G0103F000",		0,	 4700, 3450,	10000,	   25], #EPCOS10K
	["135-104LAG-J01",		0,	 4700, 3974,	100000,	   25], #Honeywell100K / QU-BD
	["104GT-2",				0,	 4700, 4267,	100000,	   25], #Semitec
]