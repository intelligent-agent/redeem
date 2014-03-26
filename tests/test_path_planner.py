import matplotlib.pyplot as plt
import numpy as np

import sys, os
lib_path = os.path.abspath('../software')
sys.path.append(lib_path)

from PathPlanner import PathPlanner
from Path import Path
from Stepper import Stepper

print "Making steppers"
steppers = {}
steppers["X"] = Stepper("GPIO0_27", "GPIO1_29", "GPIO2_4",  0, "X",None,0,0) 
steppers["Y"] = Stepper("GPIO1_12", "GPIO0_22", "GPIO2_5",  1, "Y",None,1,1)  
steppers["Z"] = Stepper("GPIO0_23", "GPIO0_26", "GPIO0_15", 2, "Z",None,2,2)  
steppers["E"] = Stepper("GPIO1_28", "GPIO1_15", "GPIO2_1",  3, "Ext1",None,3,3)
steppers["H"] = Stepper("GPIO1_13", "GPIO1_14", "GPIO2_3",  4, "Ext2",None,4,4)

path_planner = PathPlanner(steppers, None)

radius = 1.0
speed = 0.5
acceleration = 0.1
rand = 0.0

t = np.arange(0, 3*np.pi/2+(np.pi/10), np.pi/10)
rand_x = rand*np.random.uniform(-1, 1, size=len(t))
rand_y = rand*np.random.uniform(-1, 1, size=len(t))

for i in t:
    path_planner.add_path(Path({"X": radius*np.sin(i)+rand_x[i], "Y": radius*np.cos(i)+rand_y[i]}, speed, Path.ABSOLUTE, acceleration))
path_planner.add_path(Path({"X": 0.0, "Y": 0.0}, speed, Path.ABSOLUTE))
path_planner.finalize_paths()


#fig = plt.figure(figsize=(14, 9))
ax0 = plt.subplot(2, 2, 1)
plt.ylim([-1.5*radius, 1.5*radius])
plt.xlim([-1.5*radius, 1.5*radius])
plt.title('Trajectory')
speed = []
segment_max_speed = []
magnitudes = []
accel_speeds = []
decel_speeds = []
angle_speeds = []


for path in list(path_planner.paths.queue):
    ax0.arrow(path.start_pos[0], path.start_pos[1], path.vec[0], path.vec[1], 
        head_width=0.05, head_length=0.1, fc='k', ec='k',  length_includes_head=True)
    speed.append(path.start_speed)    
    magnitudes.append(path.get_magnitude())
    accel_speeds.append(path.accel_speed)
    decel_speeds.append(path.decel_speed)
    angle_speeds.append(path.angle_speed)    


positions = np.insert(np.cumsum(magnitudes[1:-1]), 0, 0)
speed = speed[1:]
accel_speeds = np.insert(accel_speeds[1:-1], 0, 0)
decel_speeds = np.append(decel_speeds[1:-1], 0)
angle_speeds = np.append(angle_speeds[1:-1], 0)

ax1 = plt.subplot(2, 2, 2)
plt.plot(positions, accel_speeds, 'r.-')
plt.plot(positions, decel_speeds, 'b.-')
plt.plot(positions, angle_speeds, 'y.-')
plt.plot(positions, speed, 'g.-')
plt.title('Velocity')

for path in list(path_planner.paths.queue):
    path_planner.do_work()

ax2 = plt.subplot(2, 2, 3)
plt.title('Acceleration')

ax2 = plt.subplot(2, 2, 4)
t = np.arange(0, 10, 0.01)
x = []
y = []
for i in t:
    x.append(16*np.power(np.sin(i), 3))
    y.append(13*np.cos(i)-5*np.cos(2*i)-2*np.cos(3*i)-np.cos(4*i))
plt.plot(x, y, 'r')
plt.ylim([-30, 30])
plt.xlim([-30, 30])

plt.title('How my 3D-printer feels')

plt.show()

