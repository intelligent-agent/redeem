#!/usr/bin/env python
"""
Redeem main program. This should run on the BeagleBone.

Author: Elias Bakken
email: elias(at)iagent(dot)no
Website: http://www.thing-printer.com
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

import glob
import logging
import logging.handlers
import numpy as np
import os
import signal
import sys
from six import PY2, iteritems
from threading import Thread
from threading import enumerate as enumerate_threads
if PY2:
  import Queue as queue
  from Queue import Empty as EmptyQueueException
else:
  import queue
  from queue import Empty as EmptyQueueException

from .Alarm import Alarm, AlarmExecutor
from .CascadingConfigParser import CascadingConfigParser
from .ColdEnd import ColdEnd
from .Cooler import Cooler
from .Delta import Delta
from .Enable import Enable
from .EndStop import EndStop
from .Ethernet import Ethernet
from .Extruder import Extruder, HBP
from .Fan import Fan
from .FilamentSensor import *
#from .Gcode import Gcode
#from .GCodeProcessor import GCodeProcessor
from .IOManager import IOManager
from .Key_pin import Key_pin, Key_pin_listener
from .Mosfet import Mosfet
#from .Path import Path
#from .PathPlanner import PathPlanner
#from .Pipe import Pipe
#from .PluginsController import PluginsController
#from .Printer import Printer
#from .PruFirmware import PruFirmware
#from .PWM import PWM
#from .RotaryEncoder import *
#from .Servo import Servo
#from .Stepper import *
#from .StepperWatchdog import StepperWatchdog
#from .TemperatureSensor import *
#from .USB import USB
#from .Watchdog import Watchdog
from .configuration import standard_configuration
# Global vars
printer = None
ControllerIsRunning = False

# Default logging level is set to debug
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
    datefmt='%m-%d %H:%M')


class TopLevelController:
  def __init__(self, *args, **kargs):
    """
    config_location: provide the location to look for config files.
     - default is installed directory
     - allows for running in a local directory when debugging
    """
    from .__init__ import __version__
    logging.info("Redeem initializing {}".format(__version__))
    global printer
    printer = "Printer()"
    self.printer = printer
    #Path.printer = printer
    #Gcode.printer = printer

    # Set up and Test the alarm framework
    Alarm.printer = self.printer
    Alarm.executor = AlarmExecutor()
    alarm = Alarm(Alarm.ALARM_TEST, "Alarm framework operational")

    standard_configuration()
    
    
def main(config_location="/etc/redeem"):
  # Create Top Level Controller
  r = TopLevelController(config_location)

  def signal_handler(signal, frame):
    logging.warning("Received signal: {}, terminating".format(signal))
    r.exit()

  def signal_logger(signal, frame):
    logging.warning("Received signal: {}, ignoring".format(signal))

  # Register signal handler to allow interrupt with CTRL-C
  signal.signal(signal.SIGINT, signal_handler)
  signal.signal(signal.SIGTERM, signal_handler)

  # Register signal handler to ignore other signals
  signal.signal(signal.SIGHUP, signal_logger)

  # Launch Redeem
  #### r.start()
  
  from redeem.configuration import ConfiguredSettings
  settings = ConfiguredSettings()
  print("**********")
  for section in settings.__dict__:
    print("[{}]".format(section))
    for key in settings.__dict__[section]:
      value = settings.__dict__[section][key]
      print("{} = {}".format(key, value))
  print("**********")

  from redeem.configuration import CurrentSettings
  CurrentSettings().put('TestSection', 'another_key', 'a_new_value')
  CurrentSettings().save()
  
  logging.info("Startup complete - main thread sleeping")

  # Wait for end of process signal
  global ControllerIsRunning
  while ControllerIsRunning:
    signal.pause()

  logging.info("Redeem Terminated")


def profile(config_location="/etc/redeem"):
  #import yappi
  #yappi.start()
  main(config_location)
  #yappi.get_func_stats().print_all()
