"""
Abstract definition for GCode command processor classes

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from abc import ABCMeta, abstractmethod
from docutils.core import publish_string
from redeem.TextWriter import text_writer


class GCodeCommand(object):
    __metaclass__ = ABCMeta

    def __init__(self, printer):
        self.printer = printer

    @abstractmethod
    def execute(self, gcode):
        pass

    @abstractmethod
    def get_description(self):
        pass

    def get_long_description(self):
        """Override method to provide long description as text."""
        # Return formatted description as plain text
        if self.get_formatted_description():
            return publish_string(self.get_formatted_description(), writer=text_writer)
        # If subclass doesn't override, return standard description
        return self.get_description()

    def get_formatted_description(self):
        """ Override method to return a full description formatted as restructured text."""
        return None

    def is_buffered(self):
        """ Return true if the command has to wait in the command buffer or
        false to be executed immediately """
        return False

    def is_sync(self):
        """ Return true if the command requires realtime synchronization with command execution """
        return False

    def is_async(self):
        """ Return true if the command executes asynchronously (such as a movement command that queues in the native path planner) """
        return False

    def __str__(self):
        """ The class name of the gcode """
        return type(self).__name__

    def get_test_gcodes(self):
        """ List of gcode strings for nose testing """
        return []
