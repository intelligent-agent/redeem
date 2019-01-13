"""
GCode G33
Autocalibrate delta printer

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
from __future__ import absolute_import
import logging
import numpy as np

from .GCodeCommand import GCodeCommand
from redeem.Gcode import Gcode


class G33(GCodeCommand):
  def execute(self, g):
    num_factors = g.get_int_by_letter("N", 4)
    if num_factors not in [3, 4, 6, 8, 9]:
      msg = "G33: Invalid number of calibration factors."
      logging.error(msg)
      self.printer.send_message(g.prot, msg)
      return

    # we reuse the G29 macro for the autocalibration purposes
    gcodes = self.printer.config.get("Macros", "G29").split("\n")
    self.printer.path_planner.wait_until_done()
    for gcode in gcodes:
      G = Gcode({"message": gcode, "parent": g})
      self.printer.processor.resolve(G)
      self.printer.processor.execute(G)
      self.printer.path_planner.wait_until_done()

    # adjust probe heights
    print_head_zs = np.array(self.printer.probe_heights[:len(self.printer.probe_points)])

    # Log the found heights
    logging.info("G33: Found heights: " + str(np.round(print_head_zs, 2)))

    simulate_only = g.has_letter("S")

    # run the actual delta autocalibration
    params = self.printer.path_planner.autocalibrate_delta_printer(
        num_factors, simulate_only, self.printer.probe_points, print_head_zs)
    logging.info("G33: Finished printer autocalibration\n")

    if g.has_letter("P"):
      # dump the dictionary to log file
      logging.debug(str(params))

      # pretty print to printer output
      self.printer.send_message(g.prot, "delta calibration : L = %g" % params["L"])
      self.printer.send_message(g.prot, "delta calibration : r = %g" % params["r"])
      self.printer.send_message(g.prot, "delta calibration : A_angular = %g" % params["A_angular"])
      self.printer.send_message(g.prot, "delta calibration : B_angular = %g" % params["B_angular"])
      self.printer.send_message(g.prot, "delta calibration : C_angular = %g" % params["C_angular"])
      self.printer.send_message(g.prot, "delta calibration : A_radial = %g" % params["A_radial"])
      self.printer.send_message(g.prot, "delta calibration : B_radial = %g" % params["B_radial"])
      self.printer.send_message(g.prot, "delta calibration : C_radial = %g" % params["C_radial"])
      self.printer.send_message(g.prot, "delta calibration : offset_x = %g" % params["offset_x"])
      self.printer.send_message(g.prot, "delta calibration : offset_y = %g" % params["offset_y"])
      self.printer.send_message(g.prot, "delta calibration : offset_z = %g" % params["offset_z"])

    return

  def get_description(self):
    return "Autocalibrate a delta printer"

  def get_long_description(self):
    return """
Do delta printer autocalibration by probing the points defined in
the G29 macro and then performing a linear least squares optimization to
minimize the regression residuals.

Parameters:

Nn  Number of factors to optimize:
    3 factors (endstop corrections only)
    4 factors (endstop corrections and delta radius) (Default and recommended)
    6 factors (endstop corrections, delta radius, and two tower
               angular position corrections)
    8 factors (endstop corrections, delta radius, two tower angular
               position corrections, and two tower radial position
               corrections)
    9 factors (endstop corrections, delta radius, two tower angular
               position corrections, two tower radial position
               corrections, and diagonal arm length)

S   Do NOT update the printer configuration.

P   Print the calculated variables"""

  def is_buffered(self):
    return True

  def is_async(self):
    return True

  def get_test_gcodes(self):
    return ["G33 F4"]