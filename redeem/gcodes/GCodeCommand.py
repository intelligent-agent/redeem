"""
Abstract definition for GCode command processor classes

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from abc import ABCMeta, abstractmethod


class GCodeCommand(object):
    __metaclass__ = ABCMeta
    
    def __init__(self, printer):
        self.printer = printer
        self.readyEvent = None

    @abstractmethod
    def execute(self, gcode):
        pass

    @abstractmethod
    def get_description(self):
        pass

    def get_long_description(self):
        return "Long description missing"

    def is_buffered(self):
        """ Return true if the command has to wait in the command buffer or
        false to be executed immediately """
        return False

    def is_sync(self):
        """ Return true if the command requires realtime synchronization with command execution """
        return False

    def __str__(self):
        """ The class name of the gcode """
        return type(self).__name__
    
    def get_test_gcodes(self):
        """ List of gcode strings for nose testing """ 
        return []
