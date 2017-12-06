"""
GCode M608
Set stepper slave mode

Author: Elias Bakken
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

import logging
from .GCodeCommand import GCodeCommand


class M608(GCodeCommand):
    def execute(self, g):
        # Not tokens returns current setup
        if g.num_tokens() == 0:
            for axis in self.printer.slaves:
                slave = self.printer.slaves[axis]
                logging.debug("Axis {} has slave '{}'".format(axis, slave))
                if slave == "":
                    self.printer.send_message(g.prot, "Axis {} does not have any slaves".format(axis))
                else:
                    self.printer.send_message(g.prot, "Axis {} has slave '{}'".format(axis, slave))
            return

        # Tokens present, process tokens
        # Non-standard GCODE formatting. Recreate tokens in old style, space delimitered fashion
        g.set_tokens(g.get_message().upper().split(" ")[1:]) # ignore the first token
        for axis in self.printer.axes_zipped:
            if g.has_letter(axis):
                slave = ""
                # get (non-RS274) second letter from gcode word, if any
                i = g.get_token_index_by_letter(axis)
                t = g.get_tokens()[i]
                if t[0] == axis and len(t)>1:
                    slave = t[1]
                if slave == "":
                    logging.info("Axis {} has no slaves".format(axis))
                    self.printer.send_message(g.prot, "Axis {} is now slaveless".format(axis))
                    self.printer.add_slave(axis, slave)
                elif not slave in self.printer.slaves:
                    logging.warning("Axis {} can not have {} as slave".format(axis, slave))
                    self.printer.send_message(g.prot, "Axis {} can not have '{}' as slave".format(axis, slave))
                else:
                    logging.info("Axis {} now has {} as slave".format(axis, slave))
                    self.printer.send_message(g.prot, "Axis {} now has '{}' as slave".format(axis, slave))
                    self.printer.add_slave(axis, slave)

        # Check to see if slaves are present
        if "".join(self.printer.slaves.values()) == "":
            self.printer.has_slaves = False

        # Update the slave configuration in path planner
        self.printer.path_planner.configure_slaves()    

    def get_description(self):
        return "Set stepper slave mode"

    def get_long_description(self):
        return ("Set stepper slave mode, making one stepper follow the other.\n"
                "If no tokens are given, return the current setup\n"
                "For each token, set the second argument as slave to the first\n"
                "So M608 XY will set Y as a slave to X\n"
                "If only the axis is given, no slave is set.")

