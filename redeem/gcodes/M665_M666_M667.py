"""
GCode M665
Set delta arm calibration values

M665 L(diagonal rod length) R(delta radius) S(segments/second)

Author: Anthony Clay
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
try:
    from Delta import Delta
except ImportError:
    from redeem.Delta import Delta
try:
    from Path import Path
except ImportError:
    from redeem.Path import Path

import logging


class M665(GCodeCommand):

    def execute(self, g):
        if g.has_letter("L"):
	    Delta.L = float(g.get_value_by_letter("L"))

	if g.has_letter("R"):
            Delta.r = float(g.get_value_by_letter("R"))
 
        if g.has_letter("S"):
                logging.info("M665 S (segments/second) specified, but not implemented.")

        #Recalcualte delta settings
	Delta.recalculate()

    def get_description(self):
        return "Set delta arm calibration values"

"""
GCode M666
Set endstop adjustment 

M666 X+0.0 Y-0.0 Z+0.0
"""

class M666(GCodeCommand):

    def execute(self, g):
        if g.has_letter("X"):
	   # Apply to X offset
           self.printer.path_planner.center_offset["X"] = float(g.get_value_by_letter("X"))

        if g.has_letter("Y"):
	   # Apply to Y offset
           self.printer.path_planner.center_offset["Y"] = float(g.get_value_by_letter("Y"))
 
        if g.has_letter("Z"):
	   # Apply to Z offset
           self.printer.path_planner.center_offset["Z"] = float(g.get_value_by_letter("Z"))


    def get_description(self):
        return "Set axis offset values"


"""
GCode M667
Set delta column adjustment 

Adjust the virtual position of delta column A, B, or C.

example:
adjust column offset of a delta column A, B, or C (X, Y, and Z axis - respectively)
M667 A X0.0 Y0.0 R0.0
Exactly one of [A,B,C], must be present.
R represents column offset. (distance along theta)
X and Y are offsets of the column, in the delta's world coordinate system.
"""

class M667(GCodeCommand):

    def execute(self, g):
        if g.has_letter("A"):

	   if g.has_letter("B") or g.has_letter("C"):
                g.set_answer("Only 1 column can be set per M667 call.")
                return
 
           if g.has_letter("X"):
                Delta.Apxe = float(g.get_value_by_letter("X"))

           if g.has_letter("Y"):
                Delta.Apye = float(g.get_value_by_letter("Y"))
 
           if g.has_letter("R"):
                Delta.Aco = float(g.get_value_by_letter("R"))

        if g.has_letter("B"):

	   if g.has_letter("A") or g.has_letter("C"):
                g.set_answer("Only 1 column can be set per M667 call.")
                return
 
           if g.has_letter("X"):
                Delta.Bpxe = float(g.get_value_by_letter("X"))

           if g.has_letter("Y"):
                Delta.Bpye = float(g.get_value_by_letter("Y"))
 
           if g.has_letter("R"):
                Delta.Bco = float(g.get_value_by_letter("R"))

        if g.has_letter("C"):

	   if g.has_letter("B") or g.has_letter("A"):
                g.set_answer("Only 1 column can be set per M667 call.")
                return
 
           if g.has_letter("X"):
                Delta.Cpxe = float(g.get_value_by_letter("X"))

           if g.has_letter("Y"):
                Delta.Cpye = float(g.get_value_by_letter("Y"))
 
           if g.has_letter("R"):
                Delta.Cco = float(g.get_value_by_letter("R"))

        Delta.recalculate()

    def get_description(self):
        return "Set delta column calibration values"



