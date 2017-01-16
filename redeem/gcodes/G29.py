"""
GCode G29
This is a macro function followed by saving the new bed matrix

Author: Elias Bakken
email: elias(dot)bakken(at)gmail dot com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
import logging
import json
import numpy as np
import copy
try:
    from Gcode import Gcode
    from Path import Path
    from Alarm import Alarm
    from BedCompensation import BedCompensation
except ImportError:
    from redeem.Gcode import Gcode
    from redeem.Path import Path
    from redeem.Alarm import Alarm
    from redeem.BedCompensation import BedCompensation

class G29(GCodeCommand):

    def execute(self, g):
        gcodes = self.printer.config.get("Macros", "G29").split("\n")
        self.printer.path_planner.wait_until_done()
        for gcode in gcodes:
            # If 'S' (imulate) remove M561 and M500 codes
            if g.has_letter("S"):
                if "RFS" in gcode:
                    logging.debug("G29: Removing due to RFS: "+str(gcode))
                else:
                    G = Gcode({"message": gcode, "prot": g.prot})
                    self.printer.processor.execute(G)
                    self.printer.path_planner.wait_until_done()
            else: # Execute all
                G = Gcode({"message": gcode, "prot": g.prot})
                self.printer.processor.execute(G)
                self.printer.path_planner.wait_until_done()

        probe_data = copy.deepcopy(self.printer.probe_points)
        bed_data = {
            "probe_data": {"x": [], "y": [], "z": []},
            "probe_type": "test" if g.has_letter("S") else "probe",
            "replicape_key": self.printer.replicape_key}
        for k, v in enumerate(probe_data):
            bed_data["probe_data"]["x"].append(probe_data[k]["X"])
            bed_data["probe_data"]["y"].append(probe_data[k]["Y"])
            bed_data["probe_data"]["z"].append(self.printer.probe_heights[k])

        Alarm.action_command("bed_probe_data", json.dumps(bed_data))

    def get_description(self):
        return "Probe the bed at specified points"

    def get_long_description(self):
        return ("Probe the bed at specified points and "
                "update the bed compensation matrix based "
                "on the found points. Add 'S' to only simulate "
                "and thus remove all lines containing the "
                "letters 'RFS' (Remove For Simulation).")

    def is_buffered(self):
        return True

    def get_test_gcodes(self):
        return ["G29"]



class G29C(GCodeCommand):

    def execute(self, g):
        bed_diameter_mm = g.get_float_by_letter("D", 140.0)     # Bed diameter
        circles = g.get_int_by_letter("C", 2)                   # Number of circles
        points_pr_circle = g.get_int_by_letter("P", 8)          # Points pr circle
        probe_start_height = g.get_float_by_letter("S", 6.0)    # Probe starting point above bed
        add_zero = bool(g.get_int_by_letter("Z", 1))            # Add probe point in 0, 0
        probe_speed = g.get_float_by_letter("K", 3000)
        reverse = g.get_int_by_letter("R", 0)
        reverse = -1 if bool(reverse) else 1

        theta = np.linspace(0, reverse*2*np.pi, points_pr_circle, endpoint=False)

        probes = []
        r = bed_diameter_mm/2
        for a in np.linspace(r, 0, circles, endpoint=False):
            for t in theta:
                x, y = a*np.cos(t), a*np.sin(t)
                probes.append((x, y))
        if add_zero:
            probes.append((0, 0))

        gcodes = "M561; (RFS) Reset bed matrix\n"
        for i, p in enumerate(probes):
            gcodes += "M557 P{0} X{1:+02.2f} Y{2:+02.2f} Z{3}\n".format(i, p[0], p[1], probe_start_height)
        gcodes += "    G32 ; Undock probe\n"
        gcodes += "    G28 ; Home steppers\n"
        for i in range(len(probes)):
            gcodes += "    G30 P{} S F{}; Probe point {}\n".format(i, probe_speed, i)
        gcodes += "    G31 ; Dock probe\n"
        gcodes += "    M561 U; (RFS) Update the matrix based on probe data\n"
        gcodes += "    M561 S; Show the current matrix\n"
        gcodes += "    M500; (RFS) Save data\n"

        # REset probe points
        self.printer.probe_points = []
        self.printer.config.set("Macros", "G29", gcodes)
        Alarm.action_command("new_g29", json.dumps(gcodes))

    def get_description(self):
        return "Generate a circular probe pattern"

    def get_long_description(self):
        return ("Generate a circular G29 Probing pattern\n"
                "D = bed_diameter_mm, default: 140\n"
                "C = Circles, default = 2\n"
                "P = points_pr_circle, default: 8\n"
                "S = probe_start_height, default: 6.0\n"
                "Z = add_zero, default = 1\n"
                "K = probe_speed, default: 3000.0\n")



class G29S(GCodeCommand):

    def execute(self, g):
        width = g.get_float_by_letter("W", 180.0)               # Bed width
        depth = g.get_float_by_letter("D", 180.0)               # Bed depth
        points = g.get_int_by_letter("P", 16)                   # Points in total
        probe_start_height = g.get_float_by_letter("S", 6.0)    # Probe starting point above bed
        probe_speed = g.get_float_by_letter("K", 3000)

        ppd = np.sqrt(points)

        probes = []
        for x in np.linspace(0, width, ppd):
            for y in np.linspace(0, depth, ppd):
                probes.append((x, y))

        gcodes = "M561; (RFS) Reset bed matrix\n"
        for i, p in enumerate(probes):
            gcodes += "M557 P{0} X{1:+02.2f} Y{2:+02.2f} Z{3}\n".format(i, p[0], p[1], probe_start_height)
        gcodes += "    G32 ; Undock probe\n"
        gcodes += "    G28 ; Home steppers\n"
        for i in range(len(probes)):
            gcodes += "    G30 P{} S F{}; Probe point {}\n".format(i, probe_speed, i)
        gcodes += "    G31 ; Dock probe\n"
        gcodes += "    M561 U; (RFS) Update the matrix based on probe data\n"
        gcodes += "    M561 S; Show the current matrix\n"
        gcodes += "    M500; (RFS) Save data\n"

        self.printer.config.set("Macros", "G29", gcodes)
        Alarm.action_command("new_g29", json.dumps(gcodes))

    def get_description(self):
        return "Generate a square probe pattern for G29"

    def get_long_description(self):
        return ("Generate a square G29 Probing pattern\n"
                "W = bed depth mm, default: 200.0\n"
                "D = bed depth mm, default: 200.0\n"
                "P = points in total, default: 16\n"
                "S = probe start height, default: 6.0\n"
                "K = probe_speed, default: 3000.0\n")
