'''
Path planner for Replicape. Just add paths to 
this and they will be executed as soon as no other 
paths are being executed. 
It's a good idea to stack up maybe five path 
segments, to have a buffer. 

Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
'''

import time
import logging
from Path import Path
import numpy as np  
from threading import Thread
import os 

try:
    from Pru import Pru
except ImportError:
    pass

try:
    import braid
except ImportError:
    pass
import Queue
from collections import defaultdict


class PathPlanner:
    ''' Init the planner '''
    def __init__(self, steppers, pru_firmware):
        self.steppers    = steppers
        if pru_firmware:
            self.pru         = Pru(pru_firmware)                 # Make the PRU
        self.paths       = Queue.Queue(100)                      # Make a queue of paths
        self.cpaths      = Queue.Queue()
        self.current_pos = {"X":0.0, "Y":0.0, "Z":0.0, "E":0.0,"H":0.0}
        self.running     = True                                 # Yes, we are running
        self.pru_data    = []
        self.t           = Thread(target=self._do_work)         # Make the thread
        self.t.daemon    = True
        self.travel_length = {"X":0.0, "Y":0.0, "Z":0.0}
        self.center_offset = {"X":0.0, "Y":0.0, "Z":0.0}
        self.prev          = None
        self.segments       = []

        if __name__ != '__main__':
            self.t.start()		 


    ''' Set travel length (printer size) for all axis '''  
    def set_travel_length(self, travel):
        self.travel_length = travel

    ''' Set offset of printer center for all axis '''  
    def set_center_offset(self, offset):
        self.center_offset = offset

    ''' Set the acceleration used '''                           # Fix me, move this to path
    def set_acceleration(self, acceleration):
        self.acceleration = acceleration

    ''' Home the given axis using endstops (min) '''
    def home(self,axis):

        if axis=="E" or axis=="H":
            return

        logging.debug("homing "+axis)
        
        p = Path({axis:-self.travel_length[axis]}, 0.01, "RELATIVE", False, False)
        p.set_homing_feedrate()

        self.add_path(p)
        path = Path({axis:-self.center_offset[axis]}, 0.01, Path.G92)
        self.add_path(path)  
        p = Path({axis:0}, 0.01, "ABSOLUTE")
        p.set_homing_feedrate()
        self.add_path(p)
        self.wait_until_done()
        logging.debug("homing done for "+axis)

    ''' Add a path segment to the path planner '''        
    def add_path(self, new):   
        print "add path"
        if new.is_G92():
            self.paths.put(new)
        else:
            # Link to the previous segment in the chain
            new.set_prev(self.prev)

            if new.movement == Path.RELATIVE:
                print "Relative segment found"                                    
                self.paths.put(new)
            else:
                if self.prev:
                    self.segments.append(self.prev)
                    # If we find an end segment, add all path segments to the queue for execution           
                    if self.prev.is_end_segment:
                        print "End segment found"                                    
                        [self.paths.put(path) for path in self.segments]
                        self.segments = []
                else:
                    self.segments = []
            self.prev = new

    ''' Add the last path to the queue for processing '''
    def finalize_paths(self):
        if self.prev:
            self.prev.finalize()
            self.segments.append(self.prev)
            [self.paths.put(path) for path in self.segments]
            self.prev = None

    ''' Return the number of paths currently on queue '''
    def nr_of_paths(self):
        return self.paths.qsize()

    ''' Set position for an axis '''
    def _set_pos(self, axis, val):
        self.current_pos[axis] = val

    '''Wait until planner is done'''
    def wait_until_done(self):
        self.paths.join()
        self.pru.wait_until_done()		 

    """ This loop pops a path, sends it to the PRU and waits for an event """
    def _do_work(self):
        while self.running:       
           self.do_work()
    
    ''' This is just a separate function so the test at the bottom will pass '''
    def do_work(self):
        path = self.paths.get()                            # Get the last path added
        path.split_into_axes()

        if path.is_G92():                                   # Only set the position of the axes
            for axis, pos in path.get_pos().iteritems():                       # Run through all the axes in the path    
                self._set_pos(axis, pos)           
            self.paths.task_done()            
            return                
        
        for axis, val in path.axes.items():                       # Run through all the axes in the path                   
            data = self._make_data(path, axis)        
            if len(data[0]) > 0:
                if len(self.pru_data) == 0:
                    self.pru_data = zip(*data)
                else:
                    self._braid_data1(self.pru_data, zip(*data))
                    #self.pru_data = self._braid_data(self.pru_data, zip(*data))
        while len(self.pru_data) > 0:  
            data = self.pru_data[0:0x10000/8]
            del self.pru_data[0:0x10000/8]
            if len(self.pru_data) > 0:
                logging.debug("Long path segment is cut. remaining: "+str(len(self.pru_data)))       
            while not self.pru.has_capacity_for(len(data)*8):          
                time.sleep(0.5)               
            self.pru.add_data(zip(*data))
            self.pru.commit_data()                            # Commit data to ddr
        
        self.pru_data = []
        
        self.paths.task_done()
        path.unlink()                                         # Remove reference to enable garbage collection

    def emergency_interrupt(self):
        self.pru.emergency_interrupt()
        while True:
            try:
                path = self.paths.get(block=False)
                if path != None:
                    self.paths.task_done()
                    path.unlink()
            except Queue.Empty:
                break

    def _braid_data(self, data1, data2):
        """ Braid/merge together the data from the two data sets"""
        return braid.braid_data_c(data1, data2)               # Use the Optimized C-function foir this. 
    
    def _braid_data1(self, data1, data2):
        """ Braid/merge together the data from the two data sets"""
        line = 0
        (pin1,dir1,o1, dly1) = data1[line]
        (pin2,dir2,o2, dly2) = data2.pop(0)
        while True: 
            dly = min(dly1, dly2)
            dly1 -= dly    
            dly2 -= dly            
            try: 
                if dly1==0 and dly2==0:
                    data1[line] = (pin1|pin2, dir1 | dir2,o1 | o2, dly)
                    (pin1,dir1,o1, dly1) = data1[line+1]
                    (pin2,dir2,o2, dly2) = data2.pop(0)
                elif dly1==0:
                    data1[line] = (pin1, dir1 ,o1 , dly)
                    (pin1,dir1,o1, dly1) = data1[line+1]
                elif dly2==0:    
                    data1.insert(line, (pin2, dir2, o2, dly))
                    (pin2,dir2,o2, dly2) = data2.pop(0)
                line += 1
            except IndexError:
                break

        if dly2 > 0:   
            #data1[line] =  (data1[line][0],data1[line][1],data1[line][2], data1[line][3]+dly2) 
            data1.append((pin2, dir2,o2, dly2)) 
            line += 1      
        elif dly1 > 0:
            data1[line] = (data1[line][0], data1[line][1],data1[line][2], data1[line][3]+dly1)  
            #data1.pop(line+1)
        
        while len(data2) > 0:
            line += 1
            (pin2,dir2,o2, dly2) = data2.pop(0)
            data1.append((pin2, dir2,o2, dly2))
        #while len(data1) > line+1:
        #    line += 1
        #    (pin1, dir1,o1, dly1) = data1[line]
        #    data1[line] = (pin2|pin1,dir1 | dir2,o1 | o2, dly1)

    ''' Join the thread '''
    def exit(self):
        self.running = False
        self.pru.join()
        self.t.join()


    def force_exit(self):
        self.running = False
        self.pru.force_exit()

    ''' Make the data for the PRU or steppers '''
    def _make_data(self, path, axis):  
        axis_nr         = Path.axis_to_index(axis)                            
        stepper         = self.steppers[axis]
        steps_pr_meter  = stepper.get_steps_pr_meter()
        num_steps       = int(path.abs_vec[axis_nr] * steps_pr_meter)      # Number of steps to tick
        if num_steps == 0:
            return ([], [])
        step_pin        = stepper.get_step_pin()                            # Get the step pin
        dir_pin         = stepper.get_dir_pin()                             # Get the direction pin
        dir_pin         = 0 if path.vec[axis_nr] < 0 else dir_pin           # Disable the dir-pin if we are going backwards  
        step_pins       = [step_pin]*num_steps                              # Make the pin states
        dir_pins        = [dir_pin]*num_steps 
        option_pins     = [path.cancellable]*num_steps                  

        ds              = 1.0/steps_pr_meter                                 # Delta S, distance in meters travelled pr step.      
        # Calculate the distance traveled when max speed is met

        if path.max_speed_starts[axis_nr] >= path.abs_vec[axis_nr]:
            print "Max speed is never met"       
            sm_start = path.switch[axis_nr]
            sm_end = path.abs_vec[axis_nr]-path.switch[axis_nr]
        else:
            print "Max speed is met after "+str(path.max_speed_starts[axis_nr])+" meters"
            sm_start = path.max_speed_starts[axis_nr]
            sm_end = path.max_speed_ends[axis_nr]
       
        distances_start  = np.arange(0, sm_start, ds)		            # Table of distances                     
        distances_end    = np.arange(0, sm_end, ds)		                # Table of distances     

        a = path.accelerations[axis_nr]
        u_start = path.start_speeds[axis_nr]
        u_end = path.end_speeds[axis_nr]
        
        timestamps_start = (-u_start+np.sqrt(2.0*a*distances_start+u_start**2))/a    # When ticks occur
        timestamps_end   = (-u_end  +np.sqrt(2.0*a*distances_end+u_end**2))/a        # When ticks occur

        timestamps_start = (-path.start_speeds[axis_nr]+np.sqrt(2.0*a*distances_start+u_start**2))/a    # When ticks occur
        timestamps_end   = (-path.end_speeds[axis_nr]  +np.sqrt(2.0*a*distances_end+u_end**2))/a        # When ticks occur

        delays_start     = np.diff(timestamps_start)/2.0			    # We are more interested in the delays pr second. 
        delays_end       = np.diff(timestamps_end)/2.0			        # We are more interested in the delays pr second.         

        i_steps     = num_steps-len(delays_start)-len(delays_end)     # Find out how many delays are missing
        i_delays    = [(ds/path.speeds[axis_nr])/2.0]*i_steps  		                    # Make the intermediate steps
        delays      = np.concatenate([delays_start, i_delays, np.flipud(delays_end)])# Add the missing delays. 
        td          = num_steps/steps_pr_meter                          # Calculate the actual travelled distance        
        if path.vec[axis_nr] < 0:                                       # If the vector is negative, negate it.      
            td     *= -1.0

        # If the axes are X or Y, we need to transform back in case of 
        # H-belt or some other transform. 
        if axis == "X" or axis == "Y":
            (td_x, td_y) = path.stepper_to_axis(td, axis)
            self.current_pos["X"] += td_x 
            self.current_pos["Y"] += td_y 
        else:                        
            self.current_pos[axis] += td                                    # Update the global position vector
        
        return (step_pins,dir_pins,option_pins, delays)                                           # return the pin states and the data



if __name__ == '__main__':
    import cProfile
    import matplotlib.pyplot as plt
    import numpy as np

    #import sys, os
    #lib_path = os.path.abspath('../software')
    #sys.path.append(lib_path)

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
    speed = 0.3
    acceleration = 0.1
    rand = 0.0

    t = np.arange(0, 3*np.pi/2+(np.pi/10), np.pi/10)
    rand_x = rand*np.random.uniform(-1, 1, size=len(t))
    rand_y = rand*np.random.uniform(-1, 1, size=len(t))

    for i in t:
        path_planner.add_path(Path({"X": radius*np.sin(i)+rand_x[i], "Y": radius*np.cos(i)+rand_y[i]}, speed, Path.ABSOLUTE, acceleration))
    path_planner.add_path(Path({"X": 0.0, "Y": 0.0}, speed, Path.ABSOLUTE))
    path_planner.add_path(Path({"X": -1.0, "Y": 1.0}, speed, Path.RELATIVE))
    path_planner.add_path(Path({"X": 1.0, "Y": -1.0}, speed, Path.RELATIVE))
    path_planner.finalize_paths()

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
        ax0.arrow(path.start_pos[0], path.start_pos[1], path.vec[0], path.vec[1], 
            head_width=0.05, head_length=0.1, fc='k', ec='k',  length_includes_head=True)
        magnitudes.append(path.get_magnitude())
        start_speeds.append(np.linalg.norm(path.start_speeds[0:1]))
        end_speeds.append(np.linalg.norm(path.end_speeds[0:1]))
        #accel_speeds.append(np.linalg.norm(path.accel_speeds[0:1]))
        #decel_speeds.append(np.linalg.norm(path.decel_speeds[0:1]))
        #angle_speeds.append(np.linalg.norm(path.angle_speeds[0:1]))
        

    positions = np.insert(np.cumsum(magnitudes), 0, 0)
    positions = np.cumsum(magnitudes)

    ax1 = plt.subplot(2, 3, 2)
    #plt.plot(positions, accel_speeds, "b")
    #plt.plot(positions, decel_speeds, "b")
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

    '''
    for name, stepper in steppers.iteritems():
            stepper.setCurrentValue(config.getfloat('Steppers', 'current_'+name)) 
            stepper.setEnabled(config.getboolean('Steppers', 'enabled_'+name)) 
            stepper.set_steps_pr_mm(config.getfloat('Steppers', 'steps_pr_mm_'+name))         
            stepper.set_microstepping(config.getint('Steppers', 'microstepping_'+name)) 
            stepper.set_decay(1) 

    # Commit changes for the Steppers
    Stepper.commit()

    Path.axis_config = int(config.get('Geometry', 'axis_config'))
    Path.max_speed_x = float(config.get('Steppers', 'max_speed_x'))
    Path.max_speed_y = float(config.get('Steppers', 'max_speed_y'))
    Path.max_speed_z = float(config.get('Steppers', 'max_speed_z'))
    Path.max_speed_e = float(config.get('Steppers', 'max_speed_e'))
    Path.max_speed_h = float(config.get('Steppers', 'max_speed_h'))


    current_pos = {"X":0.0, "Y":0.0, "Z":0.0, "E":0.0} 
    pp = Path_planner(steppers, current_pos)
    pp.set_acceleration(0.3)

    nb = 10

    print "Making paths"
    
    for x in range(nb):
        next_pos = {"Z":x*0.001} 
        path = Path(next_pos, 0.1, "ABSOLUTE", True)

        pp.add_path(path)

    print "Doing work"
    
    cProfile.run('[pp.do_work() for i in range('+str(nb)+')]', sort='time')

    print "Going back"

    next_pos = {"Z":0} 
    path = Path(next_pos, 0.1, "ABSOLUTE", False)
    pp.add_path(path)

    cProfile.run('pp.do_work()')

    pp.wait_until_done()

    for name, stepper in steppers.iteritems():
            stepper.setDisabled() 

    # Commit changes for the Steppers
    Stepper.commit()

    print "done"
    '''
    

