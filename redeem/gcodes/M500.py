"""
GCode M500
Store parameters to file

Author: Elias Bakken
email: elias(dot)bakken(at)gmail dot com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
import logging


class M500(GCodeCommand):

    def execute(self, g):
        self.printer.save_settings('/etc/redeem/local.cfg')

    def get_description(self):
        return ("Store parameters to file")

    def get_long_description(self):
        return ("Save all changed parameters to file.")

    def is_buffered(self):
        return True

    def get_test_gcodes(self):
        return ["M500"]

