"""
GCode M561 

Example: M561

This cancels any bed-plane fitting as the result of probing (or anything else) and returns the machine to moving in the user's coordinate system.

Author: Elias Bakken
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
import numpy as np
import logging


class M561(GCodeCommand):

    def execute(self, g):
        if g.has_letter("S"):
             self.printer.send_message(
            g.prot,
            "Current bed compensation matrix: {}".format(
                self.printer.matrix_bed_comp))
        else:
            self.printer.matrix_bed_comp = np.identity(3)
            self.printer.path_planner.native_planner.setBedCompensationMatrix(tuple(self.printer.matrix_bed_comp.ravel()))

    def get_description(self):
        return "Reset bed level matrix to identity"
    
    def get_long_description(self):
        return ("This cancels any bed-plane fitting as the result of probing"
                " (or anything else) and returns the machine "
                "to moving in the user's coordinate system."
                "Add 'S' to show the marix instead of resetting it.")

