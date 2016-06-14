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
import json 

try:
    from BedCompensation import BedCompensation
except ImportError:
    from redeem.BedCompensation import BedCompensation

class M561(GCodeCommand):

    def execute(self, g):
        # Show matrix
        if g.has_letter("S"):
             self.printer.send_message(
            g.prot,
            "Current bed compensation matrix: {}".format(
                json.dumps(self.printer.matrix_bed_comp.tolist() )))
            
        # Update matrix
        elif g.has_letter("U"):
            mat = BedCompensation.create_rotation_matrix(self.printer.probe_points, self.printer.probe_heights)
            self.printer.matrix_bed_comp = mat
        # Reset matrix
        else:
            self.printer.matrix_bed_comp = np.identity(3)

    def get_description(self):
        return "Show, update or reset bed level matrix to identity"
    
    def get_long_description(self):
        return ("This cancels any bed-plane fitting as the result of probing"
                " (or anything else) and returns the machine "
                "to moving in the user's coordinate system.\n"
                "Add 'S' to show the marix instead of resetting it.\n"
                "Add 'U' to update the current matrix based on probe data")

