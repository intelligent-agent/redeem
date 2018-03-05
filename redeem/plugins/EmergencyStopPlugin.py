"""
Plugin for using one of the end stop inputs as an emergecy stop button.

Author: Chad Hinton heavily leveraging the work of Elias Bakken from StartButtonPlugin.py
email: chadwhinton(at)me(dot)com
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
"""

from AbstractPlugin import AbstractPlugin
import logging
import os
try:
    from Printer import Printer
    from Key_pin import Key_pin
except ImportError:
    from redeem.Printer import Printer
    from redeem.Key_pin import Key_pin

__PLUGIN_NAME__ = 'EmergencyStop'


class EmergencyStopPlugin(AbstractPlugin):

    @staticmethod
    def get_description():
        return "Plugin to repurpose an end stop input as an emergency stop button"

    def __init__(self, printer):
        super(EmergencyStopPlugin, self).__init__(printer)

        logging.debug('Activating '+__PLUGIN_NAME__+' plugin...')

        if not self.printer.config.has_section(type(self).__name__):
            logging.error(__name__+": Missing section in config file: "+type(self).__name__)
        
        if not self.printer.config.has_option(type(self).__name__, 'end_stop_input'):
            logging.error(__name__+": Missing option: 'end_stop_input' ")
            return
            
        end_stop = self.printer.config.get(type(self).__name__, 'end_stop_input')
        if end_stop not in ["X1", "X2", "Y1", "Y2", "Z1","Z2"]:
            logging.error(__name__+": Unknown input end stop: "+str(end_stop))
            return

        if not self.printer.config.has_option(type(self).__name__, 'action'):
            logging.error(__name__+": Missing option: 'action' ")
            return

        action = self.printer.config.get(type(self).__name__, 'action')
        if action not in ["shutdownOS","restartRedeem","None"]:
            logging.error(__name__+": unknown input action: "+str(action))
            return
        
        # Disable the end-stop on this channel
        es = self.printer.end_stops[end_stop]
        es.active = False
        es.stop()

        self.printer.button = Key_pin(es.name, es.key_code)
        self.printer.button.callback = self.button_pushed


    def button_pushed(self, key, event):
        logging.debug("Emergency Stop Button pushed")

        
        action = self.printer.config.get(type(self).__name__, 'action')
        if action == "None":
            logging.debug("Emergency Stop button triggered, but no action configured.")
        if action == "shutdownOS":
            logging.info("Emergency Stop button triggered, shutting down OS.")
            os.system("shutdown -h now")
        if action == "restartRedeem":
            logging.info("Emergency Stop button triggered, restarting Redeem")
            os.system("systemctl restart redeem")
        

    def exit(self):
        pass

