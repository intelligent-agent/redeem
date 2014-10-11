"""
GCode T0 and T1
Select currently used extruder tool

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
import logging

class T0(GCodeCommand):

    def execute(self, g):
        self.printer.path_planner.set_extruder(0)
        self.printer.current_tool = "E"

    def get_description(self):
        return "Select currently used extruder tool to be T0 (E)"


    def get_test_gcodes(self):
        return ["T0"]


class T1(GCodeCommand):

    def execute(self, g):
        self.printer.path_planner.set_extruder(1)
        self.printer.current_tool = "H"

    def get_description(self):
        return "Select currently used extruder tool to be T1 (H)"

    def get_test_gcodes(self):
        return ["T1"]

class T2(GCodeCommand):

    def execute(self, g):
        self.printer.path_planner.set_extruder(2)
        self.printer.current_tool = "A"

    def get_description(self):
        return "Select currently used extruder tool to be T2 (A)"

class T3(GCodeCommand):

    def execute(self, g):
        self.printer.path_planner.set_extruder(3)
        self.printer.current_tool = "B"

    def get_description(self):
        return "Select currently used extruder tool to be T3 (B)"

class T4(GCodeCommand):

    def execute(self, g):
        self.printer.path_planner.set_extruder(4)
        self.printer.current_tool = "C"

    def get_description(self):
        return "Select currently used extruder tool to be T4 (C)"
