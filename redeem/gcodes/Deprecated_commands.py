"""
All deprecated and unsupported commands
This will silence out the command errors

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

from .GCodeCommand import GCodeCommand


class M101(GCodeCommand):

    def execute(self, g):
        pass

    def get_description(self):
        return "Deprecated"


class M103(M101):
    pass

    
class M21(M101):
    def get_long_description(self):
        return "Disabled; Redeem does not have support for SD cards."

