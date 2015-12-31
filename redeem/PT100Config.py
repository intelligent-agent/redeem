#!/usr/bin/env python
"""
Configuration for PT100 sensors. The coefficients fit in the following formula:
The coefficients are general use and represent platinum resistance sensors according
to the ITS-90

r = r0 * (1 + a*t + b*t^2) for the range 0 °C ... 850 °C

r0 is the reference resistance at 0 °C

Temperature (> 0 °C)

t = -r0*a + (r0^2*a^2 - 4*r0*b * (r0-r))^(1/2) / 2*r0*b
"""

pt100_coefficients = [
		#identifier,		r0,		a,		b,			
	["E3D-PT100-AMPLIFIER", 100,	0.0039083, -5.775e-07]
]