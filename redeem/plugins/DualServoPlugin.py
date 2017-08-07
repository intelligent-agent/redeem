"""
Plugin for using dual extruder with a servo.



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
    from Stepper import Stepper
    from Servo import Servo
    from Path import Path
    from Printer import Printer
except ImportError:
    from redeem.gcodes.GCodeCommand import GCodeCommand
    from redeem.Stepper import Stepper
    from redeem.Servo import Servo
    from redeem.Path import Path
    from redeem.Printer import Printer

__PLUGIN_NAME__ = 'DualServo'


class DualServoPlugin(AbstractPlugin):

    @staticmethod
    def get_description():
        return "Plugin to change between two hot ends that is tilted with a servo"

    def __init__(self, printer):
        super(DualServoPlugin, self).__init__(printer)

        logging.debug('Activating '+__PLUGIN_NAME__+' plugin...')

        
        # Add the servo
        channel     = self.printer.config.get(type(self).__name__, 'servo_channel')
        pulse_min   = self.printer.config.getfloat(type(self).__name__, 'pulse_min')
        pulse_max = self.printer.config.getfloat(type(self).__name__, 'pulse_max')
        angle_min = self.printer.config.getfloat(type(self).__name__, 'angle_min')
        angle_max = self.printer.config.getfloat(type(self).__name__, 'angle_max')
        angle_init = self.printer.config.getfloat(type(self).__name__, 'extruder_0_angle')

        # Disable the end-stop on this channel
        if channel == "P9_14":
            self.printer.end_stops["X2"].active = False
            self.printer.end_stops["X2"].stop()
        elif channel == "P9_16":
            self.printer.end_stops["Y2"].active = False
            self.printer.end_stops["Y2"].stop()

        self.head_servo = Servo(channel, pulse_min, pulse_max, angle_min, angle_max, angle_init)

        # Load the config for angles
        self.t0_angle = float(self.printer.config.getfloat(type(self).__name__, 'extruder_0_angle'))
        self.t1_angle = float(self.printer.config.get(type(self).__name__, 'extruder_1_angle'))

        # Override the changing tool command to trigger the servo
        self.printer.processor.override_command('T0', T0_DualServo(self.printer))
        self.printer.processor.override_command('T1', T1_DualServo(self.printer))

    def exit(self):
        self.head_servo.stop()

    def path_planner_initialized(self, path_planner):
        # Configure the path planner so that the motor direction
        # is reversed when selecting T1 or T0 (depending on the angle)

        # 3 axis, plus 2 extruders
        assert Printer.NUM_AXES >= 5

        #for i in range(2):
        #    e = self.printer.path_planner.native_planner.getExtruder(i)

            # FIXME: We have hardcoded the motor to be used here.
            #       It is always the Extruder E. Patch welcome.
        #    e.setStepperCommandPosition(3)

            # If extruder 1 angle is > 90, then we invert the motor for
            # him, otherwise for the other
            # This is how the HPX2 Max is built.
        #    if i == 0:
        #        e.setDirectionInverted(True if self.t0_angle <= 90 else False)
        #    else:
        #        e.setDirectionInverted(True if self.t1_angle <= 90 else False)

        # Select tool 0 as this is the default tool
        self.head_servo.set_angle(self.printer.plugins[__PLUGIN_NAME__].t0_angle, asynchronous=True)

class T0_DualServo(GCodeCommand):

    def execute(self, g):
        self.printer.path_planner.wait_until_done()
        self.printer.steppers["E"].set_disabled()
        self.printer.steppers["H"].set_disabled()
        Stepper.commit()
        self.printer.plugins[__PLUGIN_NAME__].head_servo.set_angle(self.printer.plugins[__PLUGIN_NAME__].t0_angle, asynchronous=False)
        self.printer.path_planner.set_extruder(0)
        self.printer.current_tool = "E"
        self.printer.steppers["E"].set_enabled()
        self.printer.steppers["H"].set_enabled()
        Stepper.commit()

    def get_description(self):
        return "Select currently used extruder tool to be T0 (E) in a DualServo Extruder"

    def is_buffered(self):
        return True


class T1_DualServo(GCodeCommand):

    def execute(self, g):
        self.printer.path_planner.wait_until_done()
        self.printer.steppers["E"].set_disabled()
        self.printer.steppers["H"].set_disabled()
        Stepper.commit()
        self.printer.plugins[__PLUGIN_NAME__].head_servo.set_angle(self.printer.plugins[__PLUGIN_NAME__].t1_angle, asynchronous=False)
        self.printer.path_planner.set_extruder(1)
        self.printer.current_tool = "H"
        self.printer.steppers["E"].set_enabled()
        self.printer.steppers["H"].set_enabled()
        Stepper.commit()

    def get_description(self):
        return "Select currently used extruder tool to be T1 (H) in aDualServo Extruder"

    def is_buffered(self):
        return True
