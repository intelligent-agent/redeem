"""
GCode G33
Autocalibrate delta printer

Author: Matti Airas
email: mairas(at)iki dot fi
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

import logging

import numpy as np

from GCodeCommand import GCodeCommand

try:
    from Gcode import Gcode
    from Path import Path
except ImportError:
    from redeem.Gcode import Gcode
    from redeem.Path import Path


class G33(GCodeCommand):

    def execute(self, g):
        num_factors = g.get_int_by_letter("F", 4)
        if num_factors < 3 or num_factors > 4:
            logging.error("G33: Invalid number of calibration factors.")

        if g.has_letter("E"):
            max_std = g.get_float_by_letter("E", 2)
        else:
            max_std = None

        # we reuse the G29 macro for the autocalibration purposes
        gcodes = self.printer.config.get("Macros", "G29").split("\n")
        self.printer.path_planner.wait_until_done()
        for gcode in gcodes:        
            G = Gcode({"message": gcode, "prot": g.prot})
            self.printer.processor.execute(G)
            self.printer.path_planner.wait_until_done()

        # adjust probe heights

        # probe heights are measured from the probing starting point
        probe_start_zs = np.array([d["Z"] for d in self.printer.probe_points])

        # this is where the probe head was when the probe was triggered
        probe_z_coords = probe_start_zs + self.printer.probe_heights
        offset_z = self.printer.config.getfloat('Probe', 'offset_z')*1000.
        # this is where the print head was when the probe was triggered
        print_head_zs = probe_z_coords - offset_z

        # Log the found heights
        logging.info("Found heights: "+str(print_head_zs))

        simulate_only = g.has_letter("S")

        # run the actual delta autocalibration
        self.printer.path_planner.autocalibrate_delta_printer(
                num_factors, max_std, simulate_only,
                self.printer.probe_points, print_head_zs)
        logging.info("Finished printer autocalibration\n")

        # FIXME: print new parameter values

    def get_description(self):
        return "Autocalibrate a delta printer"

    def get_long_description(self):
        return """
Do delta printer autocalibration by probing the points defined in
the G29 macro and then performing a linear least squares optimization to
minimize the regression residuals.

Parameters:

Fn  Number of factors to optimize:
    3 factors (endstop corrections only)
    4 factors (endstop corrections and delta radius)
    6 factors (endstop corrections, delta radius, and two tower
              angular position corrections)
    7 factors (endstop corrections, delta radius, two tower angular
              position corrections, and diagonal rod length)

En  Maximum allowed point residual as a multiplier of residual
    standard deviation. Try 2.0 for good results.

S   Do NOT update the printer configuration."""

    def is_buffered(self):
        return True

    def get_test_gcodes(self):
        return ["G33 F4"]

