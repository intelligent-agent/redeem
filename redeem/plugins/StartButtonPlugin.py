"""
Plugin for using one of the end stop inputs as a start button fro a job.

Author: Elias Bakken
email: elias(at)iagent(dot)no
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
try:
    from gcodes.GCodeCommand import GCodeCommand
    from Path import Path
    from Printer import Printer
    from Key_pin import Key_pin
except ImportError:
    from redeem.gcodes.GCodeCommand import GCodeCommand
    from redeem.Path import Path
    from redeem.Printer import Printer
    from redeem.Key_pin import Key_pin

__PLUGIN_NAME__ = 'StartButton'


class StartButtonPlugin(AbstractPlugin):

    @staticmethod
    def get_description():
        return "Plugin to repurpose an end stop input as a start button"

    def __init__(self, printer):
        super(StartButtonPlugin, self).__init__(printer)

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

        if not self.printer.config.has_option(type(self).__name__, 'gcode'):
            logging.error(__name__+": Missing option: 'gcode' ")
            return

        if not self.printer.config.has_option(type(self).__name__, 'rest_api_key'):
            logging.error(__name__+": Missing option: 'rest_api_key' ")
            return

        self._api_key = self.printer.config.get(type(self).__name__, 'rest_api_key')
        self._headers = {'Content-Type': 'application/json', 'X-Api-Key': self._api_key}
        
        # Disable the end-stop on this channel
        es = self.printer.end_stops[end_stop]
        es.active = False
        es.stop()

        self.printer.button = Key_pin(es.name, es.key_code)
        self.printer.button.callback = self.button_pushed


    def button_pushed(self, key, event):
        logging.debug("Button pushed")

        gcode = self.printer.config.get(type(self).__name__, 'gcode')
        logging.debug("Starting job: "+str(gcode))

        import requests, json

        url = "http://localhost:5000/api/files/local/"+gcode
        data = json.dumps({'command':'select', 'print': True})
        r = requests.post(url, data=data, headers=self._headers)
        if r.status_code not in [200, 204]:
            logging.error("Error starting job. Make sure the file exists and the API key is right!")
            logging.debug(r.status_code)

        

    def exit(self):
        pass

