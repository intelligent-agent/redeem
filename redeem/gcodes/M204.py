"""
GCode M204  - set default acceleration

Author: Alex Carlson
email: a.r.carlson AT me.com

License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
import logging


class M204(GCodeCommand):
    """
    M204: Set default acceleration
    Parameters (RepRapFimware) Pnnn Acceleration for printing moves Tnnn Acceleration for travel moves Example M204 P500 T2000
    Use M201 to set per-axis accelerations and extruder accelerations. RepRapFirmware applies the M204 accelerations to the move as a whole, and also applies the limits set by M201 to each axis and extruder.
    Other firmwares:
    S normal moves T filament only moves (M204 S3000 T7000) im mm/sec^2 also sets minimum segment time in ms (B20000) to prevent buffer underruns and M20 minimum feedrate
    Marlin notes: After Mar11-2015, the M204 options have changed in Marlin:
    P = Printing moves
    R = Retract only (no X, Y, Z) moves
    T = Travel (non printing) moves
    The command M204 P800 T3000 R9000 sets the acceleration for printing movements to 800mm/s^2, for travels to 3000mm/s^2 and for retracts to 9000mm/s^2.
    M204 Repetier is set PID, but tis is covered in M130-132 in Redeem.
    """

    def execute(self, g):
    # TODO: Implement set default acceleration. This is found in Slic3r Prusa i3. throws an exception and slows down
    # prints for some users.
        pass


    def get_description(self):
        return "Set default print acceleration, dummy MCode"

    # todo: fix the description of the units.
    def get_long_description(self):
        return ("Set default acceleration. Dummy MCode for now.")

    def is_buffered(self):
        return False
    
 
