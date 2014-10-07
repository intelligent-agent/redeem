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
    
    def get(self, printer_id, id = None):
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

class PrinterAPI(tornado.web.RequestHandler):

    def get(self, id = None):
        self.write({"id":0,"board_revision":current_server.printer.config.get("System","revision"), "num_extruders": 2})
     


class GCodeAPI(tornado.web.RequestHandler):

    def post(self, printer_id):

        message = tornado.escape.json_decode(self.request.body)

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

    connections = set()

    def on_open(self, info):
        # Add client to the clients list
        self.connections.add(self)

    def on_message(self, message):
        # Broadcast message
        #self.broadcast(self.connections, message)
        pass

    def on_close(self):
        # Remove client from the clients list
        self.connections.remove(self)


class RESTServer(object):

    API_PREFIX = "/api/v1.0"

    instance = None

    def __new__(theClass, *args, **kargs): 
        """ Singleton construction """
        if theClass.instance is None:
            theClass.instance = object.__new__(theClass, *args, **kargs)

        return theClass.instance

    def __init__(self, printer=None, port=None):
        global current_server

        if printer is not None and port is not None:
            self.port = port
            self.printer = printer

        if not hasattr(self,'app'):
            self.webSocketRouter = SockJSRouter(PrinterUpdateConnection, RESTServer.API_PREFIX+'/ws')

            self.app = tornado.web.Application([
                    (RESTServer.API_PREFIX+r"/printer/([0-9]+)/extruder/([A-Z])", ExtruderAPI),
                    (RESTServer.API_PREFIX+r"/printer/([0-9]+)/extruder", ExtruderAPI),
                    (RESTServer.API_PREFIX+r"/printer/([0-9]+)/gcode", GCodeAPI),
                    (RESTServer.API_PREFIX+r"/printer", PrinterAPI),
                    (RESTServer.API_PREFIX+r"/printer/([0-9]+)", PrinterAPI),
                    (r'/', tornado.web.RedirectHandler, {"url": "/static"}),
                    (r'/static', tornado.web.RedirectHandler, {"url": "/static/index.html"}),
                ] + self.webSocketRouter.urls,static_path = 'public_web', debug=True, no_keep_alive=True)

            current_server = self

            self.t = Thread(target=self._run)
            self.t.daemon = True
            self.t.start()    

    def _run(self):
        logging.info('Starting REST server on port '+str(self.port))
        self.app.listen(self.port)
        tornado.ioloop.IOLoop.instance().start()

    def _send_state_update_internal(self):
        """ Should only be run from IOLoop """
        logging.debug("Sending printer update to "+str(len(PrinterUpdateConnection.connections))+" websocket client.")
        self.webSocketRouter.broadcast(PrinterUpdateConnection.connections,"update-state")
        pass

    def send_state_update(self):
        tornado.ioloop.IOLoop.instance().add_callback(callback = lambda: self._send_state_update_internal())

    def send_message(self,message):
        pass




