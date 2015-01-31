"""
GCode T0 and T1
Select currently used extruder tool

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
from Stepper import Stepper

class T0(GCodeCommand):

    def execute(self, g):
        self.printer.path_planner.wait_until_done()
        self.printer.steppers["E"].set_disabled()
        self.printer.steppers["H"].set_disabled()
        Stepper.commit()
        self.printer.head_servo.set_angle(20, asynchronous=False)
        self.printer.path_planner.set_extruder(0)
        self.printer.current_tool = "E"
        self.printer.steppers["E"].set_enabled()
        self.printer.steppers["H"].set_enabled()
        Stepper.commit()

    def get_description(self):
        return "Select currently used extruder tool to be T0 (E)"

    def is_buffered(self):
        return True


class T1(GCodeCommand):

    def execute(self, g):
        self.printer.path_planner.wait_until_done()
        self.printer.steppers["E"].set_disabled()
        self.printer.steppers["H"].set_disabled()
        Stepper.commit()
        self.printer.head_servo.set_angle(175, asynchronous=False)
        self.printer.path_planner.set_extruder(1)
        self.printer.current_tool = "H"
        self.printer.steppers["E"].set_enabled()
        self.printer.steppers["H"].set_enabled()
        Stepper.commit()

    def get_description(self):
        return "Select currently used extruder tool to be T1 (H)"

    def is_buffered(self):
        return True


class T2(GCodeCommand):

    def execute(self, g):
        self.printer.path_planner.wait_until_done()
        self.printer.path_planner.set_extruder(2)
        self.printer.current_tool = "A"

    def get_description(self):
        return "Select currently used extruder tool to be T2 (A)"

    def is_buffered(self):
        return True
