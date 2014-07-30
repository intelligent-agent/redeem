'''
GCode processor processing GCode commands with a plugin system


Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: GNU GPL v3: http://www.gnu.org/copyleft/gpl.html

 Redeem is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.
 
 Redeem is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
 along with Redeem.  If not, see <http://www.gnu.org/licenses/>.
'''

import inspect
import logging
from gcodes import GCodeCommand

class GCodeProcessor:

    def __init__(self, printer):
        self.printer=printer

        self.gcodes={}

        module = __import__("gcodes",locals(),globals())

        self.load_classes_in_module(module)


    def load_classes_in_module(self,module):
        for name, obj in inspect.getmembers(module):
            if inspect.ismodule(obj) and obj.__name__.startswith('gcodes'):
                self.load_classes_in_module(obj)
            elif inspect.isclass(obj) and issubclass(obj,GCodeCommand.GCodeCommand) and name!='GCodeCommand':
                logging.debug("Loading GCode handler "+name+"...")
                self.gcodes[name]=obj(self.printer)

    def get_supported_commands(self):
        ret = []
        for name in self.gcodes:
            ret.append(name)

        return ret

    def get_supported_commands_and_description(self):
        ret = {}
        for name in self.gcodes:
            ret[name] = self.gcodes[name].get_description()

        return ret

    def is_buffered(self, gcode):
        val = gcode.code()
        if not val in self.gcodes:
            return False

        return self.gcodes[val].is_buffered()

    def execute(self, gcode):
        val = gcode.code()
        if not val in self.gcodes:
            logging.error("No GCode processor for "+gcode.code()+". Message: "+gcode.message)
            return None

        self.gcodes[val].execute(gcode)

        return gcode









if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')

    proc = GCodeProcessor({})

    #print proc.get_supported_commands()

    print "\nCommands:"

    descrs = proc.get_supported_commands_and_description()

    for name in descrs:
        print name+"\t\t"+descrs[name]
