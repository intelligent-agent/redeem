"""
GCode T0 and T1
Select currently used extruder tool

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

from .GCodeCommand import GCodeCommand


class ToolChange(GCodeCommand):
    def execute(self, g):
        self.printer.path_planner.set_extruder(self.tool_number)
        self.printer.current_tool = self.tool_name

    def get_description(self):
        return "Select currently used extruder tool to be T%s (%s)" % (self.tool_number, self.tool_name)

    def is_buffered(self):
        return True

    def is_async(self):
        return True

    def get_test_gcodes(self):
        return ["T%s" % (self.tool_number)]


class T0(ToolChange):
    def __init__(self, printer):
        self.tool_name = "E"
        self.tool_number = 0
        super(T0, self).__init__(printer)


class T1(ToolChange):
    def __init__(self, printer):
        self.tool_name = "H"
        self.tool_number = 1
        super(T1, self).__init__(printer)


class T2(ToolChange):
    def __init__(self, printer):
        self.tool_name = "A"
        self.tool_number = 2
        super(T2, self).__init__(printer)


class T3(ToolChange):
    def __init__(self, printer):
        self.tool_name = "B"
        self.tool_number = 3
        super(T3, self).__init__(printer)


class T4(ToolChange):
    def __init__(self, printer):
        self.tool_name = "C"
        self.tool_number = 4
        super(T4, self).__init__(printer)
