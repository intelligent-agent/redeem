"""
Abstract definition for a plugin class

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from abc import ABCMeta, abstractmethod


class abstractstatic(staticmethod):
    __slots__ = ()

    def __init__(self, function):
        super(abstractstatic, self).__init__(function)
        function.__isabstractmethod__ = True
    __isabstractmethod__ = True


class AbstractPlugin(object):
    __metaclass__ = ABCMeta

    def __init__(self, printer):
        self.printer = printer

    @abstractmethod
    def exit(self):
        pass

    @abstractstatic
    def get_description():
        return ""

    def path_planner_initialized(self, path_planner):
        """ Hook method called when the path planner has been initalized """
        pass

    def __str__(self):
        """ The class name of the plugin """
        return type(self).__name__
