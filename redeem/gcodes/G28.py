"""
GCode G28
Steppers homing

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
import logging


class G28(GCodeCommand):

    def execute(self, g):
        if g.num_tokens() == 0:  # If no token is given, home all
            g.set_tokens(["X0", "Y0", "Z0", "E0", "H0"])
        
        axis_home = []
        
        for i in range(g.num_tokens()):  # Run through all tokens
            axis = g.token_letter(i)                         
            if self.printer.config.getboolean('Endstops',
                                              'has_' + axis.lower()):
                axis_home.append(axis)     

        self.printer.path_planner.wait_until_done()
        self.printer.path_planner.home(axis_home)

        logging.info("Homing done.")
        self.printer.send_message(g.prot, "Homing done.")

    def get_description(self):
        return ("Move the steppers to their homing position "
                "(and find it as well)")

    def get_long_description(self):
        return ("This causes the RepRap machine to move back to its X, Y"
                "and Z zero endstops, a process known as 'homing'. "
                "It does so accelerating, so as to get there fast. "
                "But when it arrives it backs off by 1 mm in each "
                "direction slowly, then moves back slowly to the "
                "stop. This ensures more accurate positioning.\n"
                "If you add coordinates, then just the axes with "
                "coordinates specified will be zeroed. Thus \n"
                "G28 X0 Y72.3 \n"
                "will zero the X and Y axes, but not Z. The actual coordinate values are ignored.")

    def is_buffered(self):
        return True

    def get_test_gcodes(self):
        return ["G28"]

