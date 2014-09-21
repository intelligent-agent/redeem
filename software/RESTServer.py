#!/usr/bin/env python
"""
A class for serving reddem status and control to REST clients.
Support WebSocket connection for real time updates.

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
"""

import tornado.escape
import tornado.ioloop
import tornado.web
from tornado.escape import json_encode
from threading import Thread
from Gcode import Gcode
import logging
from sockjs.tornado import SockJSRouter, SockJSConnection

current_server = None


class ExtruderAPI(tornado.web.RequestHandler):

    Extruders = ['E','H']

    def produce_extruder_data(self,extruder):
        return {"id": extruder.name, "target_temperature":extruder.get_target_temperature(),"temperature":extruder.get_temperature()}
    
    def get(self, id = None):
        if id is None:
            ret = []
            for i in ExtruderAPI.Extruders:
                ret.append(self.produce_extruder_data(current_server.printer.heaters[i]))

            self.write({"extruders":ret})
        else:
            if id in ExtruderAPI.Extruders:
                self.write(self.produce_extruder_data(current_server.printer.heaters[id]))
            else:
                self.send_error(404)

        self.set_header("Cache-control", "no-cache")

class GCodeAPI(tornado.web.RequestHandler):

    def post(self):
        message = self.request.body

        if len(message) > 0:
            g = Gcode({"message": message, "prot": "rest"})
            if g.is_valid():
                if current_server.printer.processor.is_buffered(g):
                    current_server.printer.commands.put(g)
                else:
                    current_server.printer.unbuffered_commands.put(g)
                self.write({"ok":True})
            else:
                self.send_error(400)
           
        else:
            self.send_error(400)

        self.set_header("Cache-control", "no-cache")

class PrinterUpdateConnection(SockJSConnection):
    def on_message(self, msg):
        self.send(msg)

class RESTServer(object):

    API_PREFIX = "/api/v1.0"

    def __init__(self, printer, port):
        global current_server
        self.port = port
        self.printer = printer

        self.webSocketRouter = SockJSRouter(PrinterUpdateConnection, RESTServer.API_PREFIX+'/ws')

        self.app = tornado.web.Application([
                (RESTServer.API_PREFIX+r"/extruder/([A-Z])", ExtruderAPI),
                (RESTServer.API_PREFIX+r"/extruder", ExtruderAPI),
                (RESTServer.API_PREFIX+r"/gcode", GCodeAPI),
            ] + self.webSocketRouter.urls,debug=True)

        current_server = self

        self.t = Thread(target=self._run)
        self.t.daemon = True
        self.t.start()    

    def _run(self):
        logging.info('Starting REST server on port '+str(self.port))
        self.app.listen(self.port)
        tornado.ioloop.IOLoop.instance().start()


    def send_state_update(self):
        pass




