'''
GCode cM106
Control fans

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
'''

from AbstractGcode import AbstractGcode

# A command received from pronterface or whatever
class M106(AbstractGcode):

    def __init__(self, printer):
        self.printer=printer
        print "Init M106"




