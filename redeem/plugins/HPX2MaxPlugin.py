"""
Plugin for HPX2 Max Extruder from DGlass3D
http://www.dglass3d.com/products/hpx2max/

It allows to use a single motor for two hotends and
a servo to switch between the two hotends

The motor of the extruder has to be connected on channel 'E'

Two extruders will be created, one for 'E' and one for 'H', from the redeem
point of view.


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

from AbstractPlugin import AbstractPlugin
import logging
try:
    from gcodes.GCodeCommand import GCodeCommand
    from Stepper import Stepper
    from Servo import Servo
    from Path import Path
except ImportError:
    from redeem.gcodes.GCodeCommand import GCodeCommand
    from redeem.Stepper import Stepper
    from redeem.Servo import Servo
    from redeem.Path import Path

__PLUGIN_NAME__ = 'HPX2Max'


class HPX2MaxPlugin(AbstractPlugin):

    @staticmethod
    def get_description():
        return "Plugin to use a HPX2-Max extruder in redeem (single motor - two hotends)"

    def __init__(self, printer):
        super(HPX2MaxPlugin, self).__init__(printer)

        logging.debug('Activating '+__PLUGIN_NAME__+' plugin...')

        # Add the servo
        self.head_servo = Servo(int(self.printer.config.get(type(self).__name__, 'servo_channel', 1)),500,750,90,10) 

        # Load the config for angles
        self.t0_angle = float(self.printer.config.get(type(self).__name__, 'extruder_0_angle', 20))
        self.t1_angle = float(self.printer.config.get(type(self).__name__, 'extruder_1_angle', 175))

        # Override the changing tool command to trigger the servo
        self.printer.processor.override_command('T0', T0_HPX2Max(self.printer))
        self.printer.processor.override_command('T1', T1_HPX2Max(self.printer))

    def exit(self):
        self.head_servo.stop()

    def path_planner_initialized(self, path_planner):
        # Configure the path planner so that the motor direction
        # is reversed when selecting T1 or T0 (depending on the angle)

        # 3 axis, plus 2 extruders
        assert Path.NUM_AXES >= 5

        for i in range(2):
            e = self.printer.path_planner.native_planner.getExtruder(i)

            # FIXME: We have hardcoded the motor to be used here.
            #       It is always the Extruder E. Patch welcome.
            e.setStepperCommandPosition(3)

            # If extruder 1 angle is > 90, then we invert the motor for
            # him, otherwise for the other
            # This is how the HPX2 Max is built.
            if i == 0:
                e.setDirectionInverted(True if self.t0_angle <= 90 else False)
            else:
                e.setDirectionInverted(True if self.t1_angle <= 90 else False)

        # Select tool 0 as this is the default tool
        self.head_servo.set_angle(self.printer.plugins[__PLUGIN_NAME__].t0_angle, asynchronous=True)

class T0_HPX2Max(GCodeCommand):

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
        return "Select currently used extruder tool to be T0 (E) in a HPX2 Max Extruder"

    def is_buffered(self):
        return True


class T1_HPX2Max(GCodeCommand):

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
        return "Select currently used extruder tool to be T1 (H) in a HPX2 Max Extruder"

    def is_buffered(self):
        return True
