#!/usr/bin/env python
"""
An alarm can be executed when an error condition occurs

Author: Elias Bakken

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
from threading import Thread
import time
import logging

from multiprocessing import JoinableQueue
import Queue


class Alarm:
    THERMISTOR_ERROR = 0  # Thermistor error.
    HEATER_TOO_COLD = 1  # Temperature has fallen below the limit
    HEATER_TOO_HOT = 2  # Temperature has gone too high
    HEATER_RISING_FAST = 3  # Temperture is rising too fast
    HEATER_FALLING_FAST = 4  # Temperature is faling too fast
    FILAMENT_JAM = 5  # If filamet sensor is installed
    WATCHDOG_ERROR = 6  # Can this be detected?
    ENDSTOP_HIT = 7  # During print.
    STEPPER_FAULT = 8  # Error on a stepper
    ALARM_TEST = 9  # Testsignal, used during start-up

    printer = None
    executor = None

    def __init__(self, alarm_type, message, short_message=None):
        self.type = alarm_type
        self.message = message

        if not short_message:
            self.short_message = message
        else:
            self.short_message = short_message

        if Alarm.executor:
            Alarm.executor.queue.put(self)
        else:
            logging.error("Enable to enqueue alarm!")

    def execute(self):
        """ Execute the alarm """
        if self.type == Alarm.THERMISTOR_ERROR:
            self.stop_print()
            self.inform_listeners()
            Alarm.action_command("pause")
            Alarm.action_command("alarm_thermistor_error", self.message)
        elif self.type == Alarm.HEATER_TOO_COLD:
            self.stop_print()
            self.inform_listeners()
            Alarm.action_command("pause")
            Alarm.action_command("alarm_heater_too_cold", self.message)
        elif self.type == Alarm.HEATER_TOO_HOT:
            self.stop_print()
            self.inform_listeners()
            Alarm.action_command("pause")
            Alarm.action_command("alarm_heater_too_hot", self.message)
        elif self.type == Alarm.HEATER_RISING_FAST:
            self.stop_print()
            self.inform_listeners()
            Alarm.action_command("pause")
            Alarm.action_command("alarm_heater_rising_fast", self.message)
        elif self.type == Alarm.HEATER_FALLING_FAST:
            self.disable_heaters()
            self.inform_listeners()
            Alarm.action_command("pause")
            Alarm.action_command("alarm_heater_falling_fast", self.message)
        elif self.type == Alarm.STEPPER_FAULT:
            self.inform_listeners()
            Alarm.action_command("pause")
            Alarm.action_command("alarm_stepper_fault", self.message)
        elif self.type == Alarm.FILAMENT_JAM:
            Alarm.action_command("pause")
            Alarm.action_command("alarm_filament_jam", self.message)
        elif self.type == Alarm.ALARM_TEST:
            logging.info("Alarm: Operational")
            Alarm.action_command("alarm_operational", self.message)
        else:
            logging.warning("An Alarm of unknown type was sounded!")

    # These are the different actions that can be
    # done once an alarm is sounded.
    def stop_print(self):
        """ Stop the print """
        logging.warning("Stopping print")
        self.printer.path_planner.emergency_interrupt()
        self.disable_heaters()

    def disable_heaters(self):
        logging.warning("Disabling heaters")
        for _, heater in self.printer.heaters.iteritems():
            heater.extruder_error = True

    def inform_listeners(self):
        """ Inform all listeners (comm channels) of the occured error """
        logging.error("Alarm: "+self.message)
        if Alarm.printer and hasattr(Alarm.printer, "comms"):
            for name, comm in Alarm.printer.comms.iteritems():
                if name == "toggle":
                    comm.send_message(self.short_message)
                else:
                    comm.send_message("Alarm: "+self.message)

    @staticmethod
    def action_command(command, message=""):
        if Alarm.printer and hasattr(Alarm.printer, "comms"):
            if "octoprint" in Alarm.printer.comms:
                comm = Alarm.printer.comms["octoprint"]
                # Send action command to listeners
                if message:
                    comm.send_message("// action:{}@{}".format(command,
                                                               message))
                else:
                    comm.send_message("// action:{}".format(command))

    def make_sound(self):
        """ If a speaker is connected, sound it """
        pass

    def send_email(self):
        """ Send an e-mail to a predefined address """
        pass

    def send_sms(self):
        pass

    def record_position(self):
        """ Save last completed segment to file """
        pass


class AlarmExecutor:
    def __init__(self):
        self.queue = JoinableQueue(10)
        self.running = False
        self.t = Thread(target=self._run, name="AlarmExecutor")

    def _run(self):
        while self.running:
            try:
                alarm = self.queue.get(block=True, timeout=1)
                alarm.execute()
                logging.debug("Alarm executed")
                self.queue.task_done()
            except Queue.Empty:
                continue

    def start(self):
        logging.debug("Starting alarm executor")
        self.running = True
        self.t.start()

    def stop(self):
        if self.running:
            logging.debug("Stoppping alarm executor")
            self.running = False
            self.t.join()
        else:
            msg = "Attempted to stop alarm executor when it is not running"
            logging.debug(msg)


if __name__ == '__main__':
    logformat = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
    logging.basicConfig(level=logging.DEBUG,
                        format=logformat,
                        datefmt='%m-%d %H:%M')

    class FooPrinter:
        pass

    p = FooPrinter()
    alarm_executor = AlarmExecutor()
    Alarm.printer = p
    Alarm.executor = alarm_executor
    alarm = Alarm(Alarm.ALARM_TEST, {}, "Test")
    time.sleep(1)
    alarm_executor.stop()
