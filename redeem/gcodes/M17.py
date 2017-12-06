"""
GCode M17
Enable steppers

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

from .GCodeCommand import GCodeCommand
from six import iteritems


class M17(GCodeCommand):

    def execute(self, g):
        self.printer.path_planner.wait_until_done()
        for name, stepper in iteritems(self.printer.steppers):
            if self.printer.config.getboolean('Steppers', 'in_use_' + name):
                stepper.set_enabled()

    def get_description(self):
        return "Enable steppers"

    def get_long_description(self):
        return "Power on and enable all steppers. Motors are active after " \
               "this command."
