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

from flask import Flask
from flask.ext.restful import Api, Resource

current_server = None

class ExtruderAPI(Resource):
    def get(self, id):
        return []

class RESTServer(object):
    def __init__(self, printer, port):
        global current_server
        self.port = port
        self.printer = printer
        
        self.app = Flask(__name__)

        current_server = self

        self.app.config['SECRET_KEY'] = self.printer.config.get('System', 'rest_secret_key')
        self.api = Api(self.app, prefix='/api/v1.0')

        self.api.add_resource(ExtruderAPI, '/extruder/<int:id>', endpoint='extruder')

    def send_state_update(self):
        pass




