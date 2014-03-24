'''
GCode processor processing GCode commands with a plugin system

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
'''

import inspect
import logging
from gcodes import AbstractGcode

class GCodeProcessor:

    def __init__(self, printer):
        self.printer=printer

        self.gcodes=[]

        module = __import__("gcodes",locals(),globals())

        for name, obj in inspect.getmembers(module):
            if inspect.ismodule(obj):
                for name2, obj2 in inspect.getmembers(obj):
                    if inspect.isclass(obj2) and issubclass(obj2,AbstractGcode.AbstractGcode):
                        logging.debug("Loading GCode handler "+name2+"...")
                        self.gcodes = obj2(self.printer)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')

    proc = GCodeProcessor({})
