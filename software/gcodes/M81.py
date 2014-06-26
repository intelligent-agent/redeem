'''
GCode M81
Shutdown the whole Replicape controller board

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
'''

from GCodeCommand import GCodeCommand
import os

class M81(GCodeCommand):

    def execute(self,g):
        os.system("shutdown now")  

    def get_description(self):
        return "Shutdown the whole Replicape controller board"

    def is_buffered(self):
        return False
