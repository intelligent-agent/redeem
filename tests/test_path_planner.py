import matplotlib.pyplot as plt
import numpy as np

import sys, os
lib_path = os.path.abspath('../software')
sys.path.append(lib_path)

from PathPlanner import PathPlanner
from Path import Path, AbsolutePath, RelativePath
from Stepper import Stepper

print "Making steppers"
steppers = {}
steppers["X"] = Stepper("GPIO0_27", "GPIO1_29", "GPIO2_4",  0, "X",None,0,0) 
steppers["Y"] = Stepper("GPIO1_12", "GPIO0_22", "GPIO2_5",  1, "Y",None,1,1)  
steppers["Z"] = Stepper("GPIO0_23", "GPIO0_26", "GPIO0_15", 2, "Z",None,2,2)  
steppers["E"] = Stepper("GPIO1_28", "GPIO1_15", "GPIO2_1",  3, "Ext1",None,3,3)
steppers["H"] = Stepper("GPIO1_13", "GPIO1_14", "GPIO2_3",  4, "Ext2",None,4,4)

path_planner = PathPlanner(steppers, None)
path_planner.make_acceleration_tables()

radius = 1.0
speed = 0.3
acceleration = 0.1
rand = 0.0

t = np.arange(0, 3*np.pi/2+(np.pi/10), np.pi/10)
rand_x = rand*np.random.uniform(-1, 1, size=len(t))
rand_y = rand*np.random.uniform(-1, 1, size=len(t))

#t = np.arange(-np.pi/4, np.pi/4, 0.1)
#for i in t:
#    path_planner.add_path(AbsolutePath({"X": radius*np.sin(i)+rand_x[i], "Y": radius*np.cos(i)+rand_y[i]}, speed, acceleration))
    #path_planner.add_path(Path({"X": radius*(16*np.power(np.sin(i), 3)), "Y": radius*(13*np.cos(i)-5*np.cos(2*i)-2*np.cos(3*i)-np.cos(4*i))}, speed, Path.ABSOLUTE, acceleration))
    
path_planner.add_path(AbsolutePath({"X": 1.0, "Y": 0.3333}, speed, acceleration))
path_planner.finalize_paths()
#path_planner.add_path(RelativePath({"X": -radius, "Y": -radius}, speed, acceleration))


#fig = plt.figure(figsize=(14, 9))
ax0 = plt.subplot(2, 3, 1)
plt.ylim([-1.5*radius, 1.5*radius])
plt.xlim([-1.5*radius, 1.5*radius])
plt.title('Trajectory')
start_speeds = []
end_speeds = []
speeds = []
segment_max_speed = []
magnitudes = []
accel_speeds = []
decel_speeds = []
angle_speeds = []

mag = 0
mag_x = 0
mag_y = 0  

for path in list(path_planner.paths.queue):
    print "arrow"
    ax0.arrow(path.start_pos[0], path.start_pos[1], path.vec[0], path.vec[1], 
        head_width=0.05, head_length=0.1, fc='k', ec='k',  length_includes_head=True)
    magnitudes.append(path.get_magnitude())
    start_speeds.append(np.linalg.norm(path.start_speeds[0:1]))
    end_speeds.append(np.linalg.norm(path.end_speeds[0:1]))
    accel_speeds.append(np.linalg.norm(path.accel_speeds[0:1]))
    decel_speeds.append(np.linalg.norm(path.decel_speeds[0:1]))
    angle_speeds.append(np.linalg.norm(path.angle_speeds[0:1]))
    

positions = np.insert(np.cumsum(magnitudes), 0, 0)
positions = np.cumsum(magnitudes)

ax1 = plt.subplot(2, 3, 2)
#plt.plot(positions, accel_speeds, "b")
plt.plot(positions, decel_speeds, "b")
plt.plot(positions, end_speeds, "g")
plt.plot(positions, start_speeds, "r")
#plt.plot(positions, angle_speeds, "r")
plt.title('Velocity X')


# Acceleration
ax2 = plt.subplot(2, 3, 3)

for idx, path in enumerate(list(path_planner.paths.queue)):
    path_planner.do_work()
    plt.arrow(mag_x, path.start_speeds[0], path.abs_vec[0], path.end_speeds[0]-path.start_speeds[0], fc='g', ec='g')
    #plt.arrow(mag_y, 0.5+path.start_speeds[1], path.abs_vec[1], path.end_speeds[1]-path.start_speeds[1], fc='r', ec='r')
    
    # Plot the acceleration profile and deceleration profile
    vec_x = abs(path.vec[0])
    
    print "length: "+str(path.abs_vec[0])
    print "Switch: "+str(path.switch[0])
    s_x = np.arange(0, path.switch[0]*1.01, path.switch[0]*0.01)
    s_xd = np.arange(0, (vec_x-path.switch[0])*1.01, (vec_x-path.switch[0])*0.01)
    plt.plot(mag_x+s_x,  np.sqrt(np.square(path.start_speeds[0])+ 2*path.accelerations[0]*s_x), 'b')
    plt.plot(mag_x+s_xd+path.switch[0], 
        np.sqrt(np.square(path.start_speeds[0])+ 2*path.accelerations[0]*path.switch[0]) -
        2*path.accelerations[0]*s_xd, 'r')

    mag += abs(path.get_magnitude())
    mag_x += path.abs_vec[0]
    mag_y += abs(path.vec[1])

s = 1
u_start = 0
u_end = 0
s1 = (2*acceleration-np.square(u_start)+np.square(u_end))/(4*acceleration)

ss = np.arange(0, s1, 0.01)
sd = np.arange(s1, s, 0.01)
#plt.plot([0, s], [u_start, u_end])
#plt.plot(ss, np.sqrt(np.square(u_start)+2*acceleration*ss))
V12 = np.square(u_end)+2*acceleration*s
#plt.plot(sd, np.sqrt(V12-2*acceleration*sd))
plt.xlim([-0.1, mag_x*1.1])
plt.ylim([-0.1, 1])
plt.title('Acceleration')

# Heart
ax2 = plt.subplot(2, 3, 4)
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

