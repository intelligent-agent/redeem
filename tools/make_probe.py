"""
This script allows plotting the surface of the bed. 
"""

import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import random

# Change these parameters
bed_diameter_mm = 130 # Biggest circle
circles = 2
points_pr_circle = 8
probe_start_height = 6
add_zero = True
probe_speed = 3000
print_test_pattern = True
print_test_matrix_pattern = True
test_pattern_delay = 1000 # dealy ms
plot_result = False

theta = np.linspace(0, 2*np.pi, points_pr_circle, endpoint=False)


probes = []
r = bed_diameter_mm/2
for a in np.linspace(r, 0, circles, endpoint=False):
    for t in theta:
        x, y = a*np.cos(t), a*np.sin(t)
        probes.append((x, y))
if add_zero:
    probes.append((0, 0))
    

print """
[Macros]
G29 = 
    M561; Reset bed matrix"""
for i, p in enumerate(probes):
    print "    M557 P{0} X{1:+02.2f} Y{2:+02.2f} Z{3}".format(i, p[0], p[1], probe_start_height)
print "    G32 ; Undock probe"
print "    G28 ; Home steppers"
for i in range(len(probes)):
    print "    G30 P{} S F{}; Probe point {}".format(i, probe_speed, i)
print "    G31 ; Dock probe"
print "    M561 U; Update the matrix based on probe data" 
print "    M561 S; Show the current matrix"    

if print_test_pattern:
    print "Copy-paste this into a file called test-pattern.gcode and upload/execute"
    print "G28"
    print "G90; Absolute coordinates"
    for p in probes:
        print "G0 X{0:+02.2f} Y{1:+02.2f} Z0".format(p[0], p[1])

if print_test_matrix_pattern:
    print "Copy-paste this into a file called test-matrix.gcode and upload/execute"
    print "G28"
    print "G90; Absolute coordinates"
    print "G32"
    print "G0 Z{}".format(probe_start_height)
    for p in probes:
        print "G30 X{0:+02.2f} Y{1:+02.2f}".format(p[0], p[1])
    print "G31"


if plot_result:
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    x = []
    y = []
    z = []
    for p in probes:
        x.append(p[0])
        y.append(p[1])
        z.append(0)

    ax.plot(x, y, z, linestyle="none", marker="o", mfc="none", markeredgecolor="red")

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')

    plt.show()  


