"""
GCode G30
Single Z probe

Author: Elias Bakken
email: elias(dot)bakken(at)gmail dot com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

from .GCodeCommand import GCodeCommand
import logging
import json

from redeem.Gcode import Gcode
from redeem.Path import G92Path
from redeem.Alarm import Alarm


class G30(GCodeCommand):
  def execute(self, g):
    if g.has_letter("P"):    # Load point
      index = g.get_int_by_letter("P")
      try:
        point = self.printer.probe_points[index]
      except IndexError:
        logging.warning("G30 point P%d not yet defined. Aborting.", index)
        return
    else:
      # If no probe point is specified, use current position
      # this value is in metres
      # convert to millimetres as we are using this value for a G0 call
      point = self.printer.path_planner.get_current_pos(mm=True, ideal=True)
      logging.debug("G30: current position (mm) :  X{} Y{} Z{}".format(
          point["X"], point["Y"], point["Z"]))
    """ do not convert to SI m because used as is in gcode command, below """
    if g.has_letter("X"):    # Override X
      point["X"] = g.get_float_by_letter("X")
    if g.has_letter("Y"):    # Override Y
      point["Y"] = g.get_float_by_letter("Y")
    if g.has_letter("Z"):    # Override Z
      point["Z"] = g.get_float_by_letter("Z")

    # Get probe length, if present, else use value from config.
    if g.has_letter("D"):
      probe_length = g.get_float_by_letter("D") / 1000.
    else:
      probe_length = self.printer.config.getfloat('Probe', 'length')

    # Get probe speed, if present, else use value from config.
    if g.has_letter("F"):
      probe_speed = g.get_float_by_letter("F") / 60000.    # m/s
    else:
      probe_speed = self.printer.config.getfloat('Probe', 'speed')

    # Get acceleration, if present, else use value from config.
    if g.has_letter("Q"):
      probe_accel = g.get_float_by_letter("Q") / 3600000.    # m/s^2
    else:
      probe_accel = self.printer.config.getfloat('Probe', 'accel')

    # Find the Probe offset
    # values in config file are in metres, need to convert to millimetres
    offset_x = self.printer.config.getfloat('Probe', 'offset_x') * 1000
    offset_y = self.printer.config.getfloat('Probe', 'offset_y') * 1000
    offset_z = self.printer.config.getfloat('Probe', 'offset_z') * 1000

    logging.debug("G30: probing from point (mm) : X{} Y{} Z{}".format(
        point["X"] + offset_x, point["Y"] + offset_y, point["Z"]))

    # Move to the position
    G0 = Gcode({
        "message":
            "G0 X{} Y{} Z{}".format(point["X"] + offset_x, point["Y"] + offset_y, point["Z"]),
        "parent":
            g
    })
    self.printer.processor.resolve(G0)
    self.printer.processor.execute(G0)
    self.printer.path_planner.wait_until_done()

    bed_dist = self.printer.path_planner.probe(probe_length, probe_speed,
                                               probe_accel) * 1000.0    # convert to mm
    logging.info("G30: adjusting offset using Z-probe offset by " + str(offset_z))
    bed_dist = bed_dist - offset_z    # apply z offset
    bed_dist = round(bed_dist, 3)

    logging.debug("Bed dist: " + str(bed_dist) + " mm")

    self.printer.send_message(
        g.prot, "Found Z probe distance {0:.2f} mm at (X, Y) = ({1:.2f}, {2:.2f})".format(
            bed_dist, point["X"], point["Y"]))

    Alarm.action_command("bed_probe_point", json.dumps([point["X"], point["Y"], bed_dist]))

    # Must have S to save the probe bed distance
    # this is required for calculation of the bed compensation matrix
    # NOTE: the use of S in G30 means "save".
    if g.has_letter("S"):
      if not g.has_letter("P"):
        logging.warning("G30: S-parameter was set, but no index (P) was set.")
      else:
        self.printer.probe_heights[index] = bed_dist

  def get_description(self):
    return "Probe the bed at the current point"

  def get_long_description(self):
    return (
        "Probe the bed at the current position, or if specified, a point "
        "previously set by M557. X, Y, and Z starting probe positions can be overridden. (G20 ignored. All units in mm.)\n\n"
        "  D = sets the probe length (mm), or taken from config if nothing is specified. \n"
        "  F = sets the probe speed. If not present, it's taken from the config. \n"
        "  Q = sets the probe acceleration. If not present, it's taken from the config. \n"
        "  P = the point at which to probe, previously set by M557. \n"
        "  S = save the probed point distance\n"
        "P and S save the probed bed distance to a list that corresponds with point P")

  def is_buffered(self):
    return True

  def is_async(self):
    return True

  def get_test_gcodes(self):
    return ["G30", "G30 P0", "G30 P1 X10 Y10"]


class G30_1(GCodeCommand):
  def execute(self, g):
    # Catch most letters to tell user use may have been in error.
    if g.has_letter("P"):
      self.printer.send_message(
          g.prot, "Warning: P not supported for G30.1, proceeding as if none existed.")
    if g.has_letter("X"):    # Override X
      self.printer.send_message(
          g.prot, "Warning: X not supported for G30.1, proceeding as if none existed.")
    if g.has_letter("Y"):    # Override Y
      self.printer.send_message(
          g.prot, "Warning: Y not supported for G30.1, proceeding as if none existed.")
    if g.has_letter("Z"):    # Override Z
      Z_new = g.get_float_by_letter("Z")
    else:
      Z_new = 0

    # Usable letters listed here
    # Get probe length, if present, else use value from config.
    if g.has_letter("D"):
      probe_length = g.get_float_by_letter("D") / 1000.
    else:
      probe_length = self.printer.config.getfloat('Probe', 'length')

    # Get probe speed. If not preset, use printer's current speed.
    if g.has_letter("F"):
      probe_speed = g.get_float_by_letter("F") / 60000.0
    else:
      probe_speed = self.printer.config.getfloat('Probe', 'speed')

    # Get acceleration. If not present, use value from config.
    if g.has_letter("Q"):
      probe_accel = g.get_float_by_letter("Q") / 3600000.0
    else:
      probe_accel = self.printer.config.getfloat('Probe', 'accel')

    point = self.printer.path_planner.get_current_pos(mm=True, ideal=True)
    logging.debug("G30.1: current position (mm) :  X{} Y{} Z{}".format(
        point["X"], point["Y"], point["Z"]))
    logging.debug("G30.1: will set bed to Z{}".format(Z_new))

    # Find the Probe offset
    # values in config file are in metres, need to convert to millimetres
    offset_x = self.printer.config.getfloat('Probe', 'offset_x') * 1000
    offset_y = self.printer.config.getfloat('Probe', 'offset_y') * 1000
    offset_z = self.printer.config.getfloat('Probe', 'offset_z') * 1000

    logging.debug("G30.1: probing from point (mm) : X{} Y{} Z{}".format(
        point["X"] + offset_x, point["Y"] + offset_y, point["Z"]))

    # Move to the position
    G0 = Gcode({
        "message":
            "G0 X{} Y{} Z{}".format(point["X"] + offset_x, point["Y"] + offset_y, point["Z"]),
        "parent":
            g
    })
    self.printer.processor.resolve(G0)
    self.printer.processor.execute(G0)
    self.printer.path_planner.wait_until_done()
    bed_dist = self.printer.path_planner.probe(probe_length, probe_speed,
                                               probe_accel) * 1000.0    # convert to mm
    logging.info("G30: adjusting offset using Z-probe offset by " + str(offset_z))
    bed_dist = bed_dist - offset_z    # apply z offset

    # calculated required offset to make bed equal to Z0 or user's specified Z.
    # should be correct, assuming probe starts at Z(5), requested Z(0)  probe Z(-0.3), adjusted global Z should be 5.3
    # assuming probe starts at Z(5), and probe result is -0.3. This says real probe start was 5.3.
    # if we want to start printing at 0.2 above bed, new z should be 5.1.
    # 5 - (-0.3) - 0.2 = 5.1

    Z_adjusted = point["Z"] - bed_dist - Z_new
    logging.debug("Bed dist: " + str(bed_dist) + " mm")
    logging.debug("Old Z{}, New Z{}.".format(point["Z"], Z_adjusted))

    self.printer.send_message(g.prot, "Offsetting Z by {} to Z{}".format(bed_dist, Z_adjusted))
    # wiley's advice on bypassing sending via G92
    pos = {}
    pos["Z"] = Z_adjusted / 1000.0
    path = G92Path(pos, self.printer.feed_rate)
    self.printer.path_planner.add_path(path)

    # not sure if next part is necessary
    Alarm.action_command("bed_probe_point", json.dumps([point["X"], point["Y"], bed_dist]))

  def get_description(self):
    return "Probes the bed at the current point, sets Z0."

  def get_long_description(self):
    return ("Probe the bed at the current position. (G20 ignored. All units in mm.)"
            "X, Y, P and S inputs are ignored. \n"
            "Z = sets the requested Z height at bed level, if not present, set to 0. \n"
            "D = sets the probe length, or taken from config if nothing is specified. \n"
            "F = sets the probe speed. If not present, it's taken from the config. \n"
            "Q = sets the probe acceleration. If not present, it's taken from the config. \n")

  def is_buffered(self):
    return True

  # What should be put here?
  def get_test_gcodes(self):
    return ["G30.1", "G30.1 P0", "G30.1 P1 X10 Y10 Z10"]
