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
import importlib
import inspect
import logging
import logging.handlers
import os
import os.path
import signal
import threading
from threading import Thread
import Queue
import numpy as np
import sys
import boards.probe

from Mosfet import Mosfet
from Stepper import *
from TemperatureSensor import *
from Fan import Fan
from Servo import Servo
from EndStop import EndStop
from USB import USB
from Pipe import Pipe
from Ethernet import Ethernet
from Extruder import Extruder, HBP
from Cooler import Cooler
from Path import Path
from PathPlanner import PathPlanner
from Gcode import Gcode
from ColdEnd import ColdEnd
from PruFirmware import PruFirmware
from CascadingConfigParser import CascadingConfigParser
from Printer import Printer
from GCodeProcessor import GCodeProcessor
from PluginsController import PluginsController
from Delta import Delta
from Enable import Enable
from PWM import PWM
from RotaryEncoder import *
from FilamentSensor import *
from Alarm import Alarm, AlarmExecutor
from StepperWatchdog import StepperWatchdog
from Key_pin import Key_pin, Key_pin_listener
from Watchdog import Watchdog
from six import iteritems

# Global vars
printer = None
RedeemIsRunning = False

# Default logging level is set to debug
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
    datefmt='%m-%d %H:%M')


class Redeem:
  def __init__(self, config_location="/etc/redeem"):
    """
    config_location: provide the location to look for config files.
     - default is installed directory
     - allows for running in a local directory when debugging
    """
    from __init__ import __version__
    logging.info("Redeem initializing {}".format(__version__))

    global printer
    printer = Printer()
    self.printer = printer
    Path.printer = printer
    Gcode.printer = printer

    # Set up and Test the alarm framework
    Alarm.printer = self.printer
    Alarm.executor = AlarmExecutor()
    alarm = Alarm(Alarm.ALARM_TEST, "Alarm framework operational")

    # check for config files
    file_path = os.path.join(config_location, "default.cfg")
    if not os.path.exists(file_path):
      logging.error(file_path + " does not exist, this file is required for operation")
      sys.exit()    # maybe use something more graceful?

    local_path = os.path.join(config_location, "local.cfg")
    if not os.path.exists(local_path):
      logging.info(local_path + " does not exist, Creating one")
      os.mknod(local_path)
      os.chmod(local_path, 0o666)

    # Parse the config files.
    printer.config = CascadingConfigParser([
        os.path.join(config_location, 'default.cfg'),
        os.path.join(config_location, 'printer.cfg'),
        os.path.join(config_location, 'local.cfg')
    ])

    # Check the local and printer files
    printer_path = os.path.join(config_location, "printer.cfg")
    if os.path.exists(printer_path):
      printer.config.check(printer_path)
    printer.config.check(os.path.join(config_location, 'local.cfg'))

    # Get the loglevel from the Config file
    level = self.printer.config.getint('System', 'loglevel')
    if level > 0:
      logging.getLogger().setLevel(level)

    # Set up additional logging, if present:
    if self.printer.config.getboolean('System', 'log_to_file'):
      logfile = self.printer.config.get('System', 'logfile')
      formatter = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
      printer.redeem_logging_handler = logging.handlers.RotatingFileHandler(
          logfile, maxBytes=2 * 1024 * 1024)
      printer.redeem_logging_handler.setFormatter(logging.Formatter(formatter))
      printer.redeem_logging_handler.setLevel(level)
      logging.getLogger().addHandler(printer.redeem_logging_handler)
      logging.info("-- Logfile configured --")

    # probe for the actual hardware
    boards.probe.probe_all_boards(self.printer)

    if hasattr(self.printer, "board"):
      logging.info("Found board: %s %s", self.printer.board, self.printer.revision)
    else:
      logging.error("No printer control board found - exiting")
      sys.exit()

    # Init the Watchdog timer
    printer.watchdog = Watchdog()

    printer.NUM_EXTRUDERS = printer.config.getint('Steppers', 'number_of_extruders')

    printer.axis_config = printer.config.getint('Geometry', 'axis_config')

    homing_only_endstops = self.printer.config.get('Endstops', 'homing_only_endstops')

    for es in ["Z2", "Y2", "X2", "Z1", "Y1",
               "X1"]:    # Order matches end stop inversion mask in Firmware
      pin = self.printer.end_stop_inputs[es]
      keycode = self.printer.end_stop_keycodes[es]
      invert = self.printer.config.getboolean("Endstops", "invert_" + es)
      self.printer.end_stops[es] = EndStop(printer, pin, keycode, es, invert)
      self.printer.end_stops[es].stops = printer.config.get('Endstops', 'end_stop_' + es + '_stops')

    # activate all the endstops
    self.printer.set_active_endstops()

    # Init the 5 Stepper motors (step, dir, fault, DAC channel, name)
    Stepper.printer = printer

    # Enable the steppers and set the current, steps pr mm and
    # microstepping
    for name, stepper in iteritems(self.printer.steppers):
      stepper.in_use = printer.config.getboolean('Steppers', 'in_use_' + name)
      stepper.direction = printer.config.getint('Steppers', 'direction_' + name)
      stepper.has_endstop = printer.config.getboolean('Endstops', 'has_' + name)
      stepper.set_current_value(printer.config.getfloat('Steppers', 'current_' + name))
      stepper.set_steps_pr_mm(printer.config.getfloat('Steppers', 'steps_pr_mm_' + name))
      stepper.set_microstepping(printer.config.getint('Steppers', 'microstepping_' + name))
      stepper.set_decay(printer.config.getint("Steppers", "slow_decay_" + name))
      # Add soft end stops
      printer.soft_min[Printer.axis_to_index(name)] = printer.config.getfloat(
          'Endstops', 'soft_end_stop_min_' + name)
      printer.soft_max[Printer.axis_to_index(name)] = printer.config.getfloat(
          'Endstops', 'soft_end_stop_max_' + name)
      slave = printer.config.get('Steppers', 'slave_' + name)
      if slave:
        printer.add_slave(name, slave)
        logging.debug("Axis " + name + " has slave " + slave)

    # Commit changes for the Steppers
    #Stepper.commit()

    Stepper.printer = printer

    # Delta printer setup
    if printer.axis_config == Printer.AXIS_CONFIG_DELTA:
      opts = ["L", "r", "A_radial", "B_radial", "C_radial", "A_angular", "B_angular", "C_angular"]
      for opt in opts:
        Delta.__dict__[opt] = printer.config.getfloat('Delta', opt)

    # Discover and add all DS18B20 cold ends.
    paths = glob.glob("/sys/bus/w1/devices/28-*/w1_slave")
    logging.debug("Found cold ends: " + str(paths))
    for i, path in enumerate(paths):
      self.printer.cold_ends.append(ColdEnd(path, "ds18b20-" + str(i)))
      logging.info("Found Cold end " + str(i) + " on " + path)

    # Make Mosfets, temperature sensors and extruders
    heaters = ["E", "H", "HBP"]
    for e in heaters:
      # Thermistors
      adc = self.printer.thermistor_inputs[e]
      if not self.printer.config.has_option("Heaters", "sensor_" + e):
        sensor = self.printer.config.get("Heaters", "temp_chart_" + e)
        logging.warning("Deprecated config option temp_chart_" + e + " use sensor_" + e +
                        " instead.")
      else:
        sensor = self.printer.config.get("Heaters", "sensor_" + e)
      self.printer.thermistors[e] = TemperatureSensor(adc, 'MOSFET ' + e, sensor)
      self.printer.thermistors[e].printer = printer

      # Extruders
      onoff = self.printer.config.getboolean('Heaters', 'onoff_' + e)
      prefix = self.printer.config.get('Heaters', 'prefix_' + e)
      if e != "HBP":
        self.printer.heaters[e] = Extruder(self.printer.steppers[e], self.printer.thermistors[e],
                                           self.printer.mosfets[e], e, onoff)
      else:
        self.printer.heaters[e] = HBP(self.printer.thermistors[e], self.printer.mosfets[e], onoff)
      self.printer.heaters[e].prefix = prefix
      self.printer.heaters[e].Kp = self.printer.config.getfloat('Heaters', 'pid_Kp_' + e)
      self.printer.heaters[e].Ti = self.printer.config.getfloat('Heaters', 'pid_Ti_' + e)
      self.printer.heaters[e].Td = self.printer.config.getfloat('Heaters', 'pid_Td_' + e)

      # Min/max settings
      self.printer.heaters[e].min_temp = self.printer.config.getfloat('Heaters', 'min_temp_' + e)
      self.printer.heaters[e].max_temp = self.printer.config.getfloat('Heaters', 'max_temp_' + e)
      self.printer.heaters[e].max_temp_rise = self.printer.config.getfloat(
          'Heaters', 'max_rise_temp_' + e)
      self.printer.heaters[e].max_temp_fall = self.printer.config.getfloat(
          'Heaters', 'max_fall_temp_' + e)
      self.printer.heaters[e].max_power = self.printer.config.getfloat('Heaters', 'max_power_' + e)

    # Set default value for all fans
    for i, f in enumerate(self.printer.fans):
      f.set_value(self.printer.config.getfloat('Fans', "default-fan-{}-value".format(i)))

    # Init the servos
    printer.servos = []
    servo_nr = 0
    while (printer.config.has_option("Servos", "servo_" + str(servo_nr) + "_enable")):
      if printer.config.getboolean("Servos", "servo_" + str(servo_nr) + "_enable"):
        channel = printer.config.get("Servos", "servo_" + str(servo_nr) + "_channel")
        pulse_min = printer.config.getfloat("Servos", "servo_" + str(servo_nr) + "_pulse_min")
        pulse_max = printer.config.getfloat("Servos", "servo_" + str(servo_nr) + "_pulse_max")
        angle_min = printer.config.getfloat("Servos", "servo_" + str(servo_nr) + "_angle_min")
        angle_max = printer.config.getfloat("Servos", "servo_" + str(servo_nr) + "_angle_max")
        angle_init = printer.config.getfloat("Servos", "servo_" + str(servo_nr) + "_angle_init")
        s = Servo(channel, pulse_min, pulse_max, angle_min, angle_max, angle_init)
        printer.servos.append(s)
        logging.info("Added servo " + str(servo_nr))
      servo_nr += 1

    # Connect thermistors to fans
    for t, therm in iteritems(self.printer.heaters):
      for f, fan in enumerate(self.printer.fans):
        if not self.printer.config.has_option('Cold-ends', "connect-therm-{}-fan-{}".format(t, f)):
          continue
        if printer.config.getboolean('Cold-ends', "connect-therm-{}-fan-{}".format(t, f)):
          c = Cooler(therm, fan, "Cooler-{}-{}".format(t, f), True)    # Use ON/OFF on these.
          c.ok_range = 4
          opt_temp = "therm-{}-fan-{}-target_temp".format(t, f)
          if printer.config.has_option('Cold-ends', opt_temp):
            target_temp = printer.config.getfloat('Cold-ends', opt_temp)
          else:
            target_temp = 60
          c.set_target_temperature(target_temp)
          max_speed = "therm-{}-fan-{}-max_speed".format(t, f)
          if printer.config.has_option('Cold-ends', max_speed):
            target_speed = printer.config.getfloat('Cold-ends', max_speed)
          else:
            target_speed = 1.0
          c.set_max_speed(target_speed)
          c.enable()
          printer.coolers.append(c)
          logging.info("Cooler connects therm {} with fan {}".format(t, f))

    # Connect fans to M106
    printer.controlled_fans = []
    for i, fan in enumerate(self.printer.fans):
      if not self.printer.config.has_option('Cold-ends', "add-fan-{}-to-M106".format(i)):
        continue
      if self.printer.config.getboolean('Cold-ends', "add-fan-{}-to-M106".format(i)):
        printer.controlled_fans.append(self.printer.fans[i])
        logging.info("Added fan {} to M106/M107".format(i))

    # Connect the colds to fans
    for ce, cold_end in enumerate(self.printer.cold_ends):
      for f, fan in enumerate(self.printer.fans):
        option = "connect-ds18b20-{}-fan-{}".format(ce, f)
        if self.printer.config.has_option('Cold-ends', option):
          if self.printer.config.getboolean('Cold-ends', option):
            c = Cooler(cold_end, fan, "Cooler-ds18b20-{}-{}".format(ce, f), False)
            c.ok_range = 4
            opt_temp = "cooler_{}_target_temp".format(ce)
            if printer.config.has_option('Cold-ends', opt_temp):
              target_temp = printer.config.getfloat('Cold-ends', opt_temp)
            else:
              target_temp = 60
            c.set_target_temperature(target_temp)
            c.enable()
            printer.coolers.append(c)
            logging.info("Cooler connects temp sensor ds18b20 {} with fan {}".format(ce, f))

    # Init encoders
    printer.filament_sensors = []
    printer.rotary_encoders = []
    for ex in ["E", "H", "A", "B", "C"]:
      if not printer.config.has_option('Rotary-encoders', "enable-{}".format(ex)):
        continue
      if printer.config.getboolean("Rotary-encoders", "enable-{}".format(ex)):
        logging.debug("Rotary encoder {} enabled".format(ex))
        event = printer.config.get("Rotary-encoders", "event-{}".format(ex))
        cpr = printer.config.getint("Rotary-encoders", "cpr-{}".format(ex))
        diameter = printer.config.getfloat("Rotary-encoders", "diameter-{}".format(ex))
        r = RotaryEncoder(event, cpr, diameter)
        printer.rotary_encoders.append(r)
        # Append as Filament Sensor
        ext_nr = Printer.axis_to_index(ex) - 3
        sensor = FilamentSensor(ex, r, ext_nr, printer)
        alarm_level = printer.config.getfloat("Filament-sensors", "alarm-level-{}".format(ex))
        logging.debug("Alarm level" + str(alarm_level))
        sensor.alarm_level = alarm_level
        printer.filament_sensors.append(sensor)

    # Make a queue of commands
    self.printer.commands = Queue.Queue(10)

    # Make a queue of commands that should not be buffered
    self.printer.unbuffered_commands = Queue.Queue(10)

    # Bed compensation matrix
    printer.matrix_bed_comp = printer.load_bed_compensation_matrix()
    logging.debug("Loaded bed compensation matrix: \n" + str(printer.matrix_bed_comp))

    for axis in printer.steppers.keys():
      i = Printer.axis_to_index(axis)
      printer.max_speeds[i] = printer.config.getfloat('Planner', 'max_speed_' + axis.lower())
      printer.max_speed_jumps[i] = printer.config.getfloat('Planner', 'max_jerk_' + axis.lower())
      printer.home_speed[i] = printer.config.getfloat('Homing', 'home_speed_' + axis.lower())
      printer.home_backoff_speed[i] = printer.config.getfloat('Homing',
                                                              'home_backoff_speed_' + axis.lower())
      printer.home_backoff_offset[i] = printer.config.getfloat(
          'Homing', 'home_backoff_offset_' + axis.lower())
      printer.steps_pr_meter[i] = printer.steppers[axis].get_steps_pr_meter()
      printer.backlash_compensation[i] = printer.config.getfloat('Steppers',
                                                                 'backlash_' + axis.lower())

    printer.e_axis_active = printer.config.getboolean('Planner', 'e_axis_active')

    dirname = os.path.dirname(os.path.realpath(__file__))

    # Create the firmware compiler
    pru_firmware = PruFirmware(
        dirname + "/firmware/firmware_runtime.c", dirname + "/firmware/firmware_runtime.bin",
        dirname + "/firmware/firmware_endstops.c", dirname + "/firmware/firmware_endstops.bin",
        self.printer, "/usr/bin/clpru", dirname + "/firmware/AM335x_PRU.cmd",
        dirname + "/firmware/image.cmd")

    printer.move_cache_size = printer.config.getfloat('Planner', 'move_cache_size')
    printer.print_move_buffer_wait = printer.config.getfloat('Planner', 'print_move_buffer_wait')
    printer.max_buffered_move_time = printer.config.getfloat('Planner', 'max_buffered_move_time')

    self.printer.processor = GCodeProcessor(self.printer)
    self.printer.plugins = PluginsController(self.printer)

    # Path planner
    travel_default = False
    center_default = False
    home_default = False

    # Setting acceleration before PathPlanner init
    for axis in printer.steppers.keys():
      printer.acceleration[Printer.axis_to_index(axis)] = printer.config.getfloat(
          'Planner', 'acceleration_' + axis.lower())

    self.printer.path_planner = PathPlanner(self.printer, pru_firmware)
    for axis in printer.steppers.keys():
      i = Printer.axis_to_index(axis)

      # Sometimes soft_end_stop aren't defined to be at the exact hardware boundary.
      # Adding 100mm for searching buffer.
      if printer.config.has_option('Geometry', 'travel_' + axis.lower()):
        printer.path_planner.travel_length[axis] = printer.config.getfloat(
            'Geometry', 'travel_' + axis.lower())
      else:
        printer.path_planner.travel_length[axis] = (printer.soft_max[i] - printer.soft_min[i]) + .1
        if axis in ['X', 'Y', 'Z']:
          travel_default = True

      if printer.config.has_option('Geometry', 'offset_' + axis.lower()):
        printer.path_planner.center_offset[axis] = printer.config.getfloat(
            'Geometry', 'offset_' + axis.lower())
      else:
        printer.path_planner.center_offset[axis] = (printer.soft_min[i] if printer.home_speed[i] > 0
                                                    else printer.soft_max[i])
        if axis in ['X', 'Y', 'Z']:
          center_default = True

      if printer.config.has_option('Homing', 'home_' + axis.lower()):
        printer.path_planner.home_pos[axis] = printer.config.getfloat('Homing',
                                                                      'home_' + axis.lower())
      else:
        printer.path_planner.home_pos[axis] = printer.path_planner.center_offset[axis]
        if axis in ['X', 'Y', 'Z']:
          home_default = True

    if printer.axis_config == Printer.AXIS_CONFIG_DELTA:
      if travel_default:
        logging.warning(
            "Axis travel (travel_*) set by soft limits, manual setup is recommended for a delta")
      if center_default:
        logging.warning(
            "Axis offsets (offset_*) set by soft limits, manual setup is recommended for a delta")
      if home_default:
        logging.warning("Home position (home_*) set by soft limits or offset_*")
        logging.info("Home position will be recalculated...")

        # convert home_pos to effector space
        Az = printer.path_planner.home_pos['X']
        Bz = printer.path_planner.home_pos['Y']
        Cz = printer.path_planner.home_pos['Z']

        delta_bot = self.printer.path_planner.native_planner.delta_bot

        z_offset = delta_bot.verticalOffset(Az, Bz, Cz)    # vertical offset
        xyz = delta_bot.deltaToWorld(Az, Bz, Cz)    # effector position

        # The default home_pos, provided above, is based on effector space
        # coordinates for carriage positions. We need to transform these to
        # get where the effector actually is.
        xyz[2] += z_offset
        for i, a in enumerate(['X', 'Y', 'Z']):
          printer.path_planner.home_pos[a] = xyz[i]

        logging.info("Home position = %s" % str(printer.path_planner.home_pos))

    # Read end stop value again now that PRU is running
    for _, es in iteritems(self.printer.end_stops):
      es.read_value()

    # Enable Stepper timeout
    timeout = printer.config.getint('Steppers', 'timeout_seconds')
    printer.swd = StepperWatchdog(printer, timeout)
    if printer.config.getboolean('Steppers', 'use_timeout'):
      printer.swd.start()

    # Set up communication channels
    printer.comms["USB"] = USB(self.printer)
    printer.comms["Eth"] = Ethernet(self.printer)
    printer.comms["octoprint"] = Pipe(printer, "octoprint")
    printer.comms["toggle"] = Pipe(printer, "toggle")
    printer.comms["testing"] = Pipe(printer, "testing")
    printer.comms["testing_noret"] = Pipe(printer, "testing_noret")
    # Does not send "ok"
    printer.comms["testing_noret"].send_response = False

  def start(self):
    """ Start the processes """
    global RedeemIsRunning
    RedeemIsRunning = True
    # Start the two processes
    p0 = Thread(target=self.loop, args=(self.printer.commands, "buffered"), name="p0")
    p1 = Thread(target=self.loop, args=(self.printer.unbuffered_commands, "unbuffered"), name="p1")
    p0.daemon = True
    p1.daemon = True

    p0.start()
    p1.start()

    Alarm.executor.start()
    Key_pin.listener.start()

    if self.printer.config.getboolean('Watchdog', 'enable_watchdog'):
      self.printer.watchdog.start()

    self.printer.enable.set_enabled()

    # Signal everything ready
    logging.info("Redeem ready")

  def loop(self, queue, name):
    """ When a new gcode comes in, execute it """
    try:
      while RedeemIsRunning:
        try:
          gcode = queue.get(block=True, timeout=1)
        except Queue.Empty:
          continue
        logging.debug("Executing " + gcode.code() + " from " + name + " " + gcode.message)
        self._execute(gcode)
        self.printer.reply(gcode)
        queue.task_done()
        logging.debug("Completed " + gcode.code() + " from " + name + " " + gcode.message)
    except Exception:
      logging.exception("Exception in {} loop: ".format(name))

  def exit(self):
    global RedeemIsRunning
    if not RedeemIsRunning:
      return
    RedeemIsRunning = False
    logging.info("Redeem Shutting Down")
    printer.path_planner.wait_until_done()
    printer.path_planner.force_exit()

    # Stops plugins
    self.printer.plugins.exit()

    for name, stepper in iteritems(self.printer.steppers):
      stepper.set_disabled()
    Stepper.commit()

    for name, heater in iteritems(self.printer.heaters):
      logging.debug("closing " + name)
      heater.disable()

    for name, endstop in iteritems(self.printer.end_stops):
      logging.debug("terminating " + name)
      endstop.stop()

    for name, comm in iteritems(self.printer.comms):
      logging.debug("closing " + name)
      comm.close()

    self.printer.enable.set_disabled()
    self.printer.swd.stop()
    Alarm.executor.stop()
    Key_pin.listener.stop()
    self.printer.watchdog.stop()
    self.printer.enable.set_disabled()

    # list all threads that are still running
    # note: some of these maybe daemons
    for t in threading.enumerate():
      logging.debug("Thread " + t.name + " is still running")
    logging.info("Redeem Exit Complete")

  def _execute(self, g):
    """ Execute a G-code """
    if g.message == "ok" or g.code() == "ok" or g.code() == "No-Gcode":
      g.set_answer(None)
      return
    if g.is_info_command():
      desc = self.printer.processor.get_long_description(g)
      self.printer.send_message(g.prot, desc)
    else:
      self.printer.processor.execute(g)

  def _synchronize(self, g):
    """ Synchronized execution of a G-code """
    self.printer.processor.synchronize(g)


def main(config_location="/etc/redeem"):
  # Create Redeem
  r = Redeem(config_location)

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
  r.start()

  logging.info("Startup complete - main thread sleeping")

  # Wait for end of process signal
  global RedeemIsRunning
  while RedeemIsRunning:
    signal.pause()

  logging.info("Main thread terminating")


def profile(config_location="/etc/redeem"):
  import yappi
  yappi.start()
  main(config_location)
  yappi.get_func_stats().print_all()


if __name__ == '__main__':
  if len(sys.argv) > 1 and sys.argv[1] == "profile":
    profile()
  else:
    main()
