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
        meters_pr_steps = np.ones(Path.NUM_AXES)
        distances = np.cumsum([meters_pr_steps]*10000)

    ''' Get the current pos as a dict '''
    def get_current_pos(self):
        pos = np.zeros(Path.NUM_AXES)
        if self.prev:
            pos = self.prev.end_pos        
        pos2 = {}
        for index, axis in enumerate(Path.AXES):
            pos2[axis] = pos[index]

        return pos2
            

    ''' Home the given axis using endstops (min) '''
    def home(self,axis):

        if axis=="E" or axis=="H":
            return

        logging.debug("homing "+axis)
        speed = Path.home_speed[Path.axis_to_index(axis)]
        # Move until endstop is hit
        p = Path({axis:-self.travel_length[axis]}, speed, Path.RELATIVE)
        self.add_path(p)

        # Reset position to offset
        path = Path({axis:-self.center_offset[axis]}, speed, Path.G92)
        self.add_path(path)  
        
        # Move to offset
        p = Path({axis:0}, speed, Path.ABSOLUTE)
        self.add_path(p)
        self.finalize_paths()
        self.wait_until_done()
        logging.debug("homing done for "+axis)

    ''' Add a path segment to the path planner '''        
    def add_path(self, new):   
        # Link to the previous segment in the chain
        new.set_prev(self.prev)

        if self.prev and not self.prev.is_added:
            self.segments.append(self.prev)
            self.prev.is_added = True
            # If we find an end segment, add all path segments to the queue for execution           
            if self.prev.is_end_segment:
                logging.debug("Processing all segments on queue!")
                [self.paths.put(path) for path in self.segments]
                self.segments = []
        self.prev = new
        
        # If this is a relative move or G92, add it right away
        if new.is_end_segment:
            self.paths.put(new)
            new.is_added = True
            self.segments = []

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

        if path.is_G92():                                   # Only set the position of the axes
            #for axis, pos in path.axes.iteritems():                       # Run through all the axes in the path    
            #    self._set_pos(axis, pos)           
            self.paths.task_done()            
            return                
        # Make the accleration profiles
        path.split_into_axes()
        
        for axis, val in path.axes.items():                       # Run through all the axes in the path                   
            data = self._make_data(path, axis)        
            if len(data[0]) > 0:
                if len(self.pru_data) == 0:
                    self.pru_data = zip(*data)
                else:
                    self._braid_data1(self.pru_data, zip(*data))
                    #self.pru_data = self._braid_data(self.pru_data, zip(*data))
        while len(self.pru_data) > 0:  
            data = self.pru_data[0:0x20000/8]
            del self.pru_data[0:0x20000/8]
            if len(self.pru_data) > 0:
                logging.debug("Long path segment is cut. remaining: "+str(len(self.pru_data)))       
            if hasattr(self, 'pru'):
                while not self.pru.has_capacity_for(len(data)*8):          
                    time.sleep(0.5)               
                self.pru.add_data(zip(*data))
                self.pru.commit_data()                            # Commit data to ddr
            logging.debug("Added segment to pru")
        
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
        logging.debug("Processing "+axis+" of len "+str(path.abs_vec[axis_nr]))
        step_pin        = stepper.get_step_pin()                            # Get the step pin
        dir_pin         = stepper.get_dir_pin()                             # Get the direction pin
        dir_pin         = 0 if path.vec[axis_nr] < 0 else dir_pin           # Disable the dir-pin if we are going backwards  
        step_pins       = [step_pin]*num_steps                              # Make the pin states
        dir_pins        = [dir_pin]*num_steps 
        option_pins     = [path.cancellable]*num_steps                  

        # Calculate the distance traveled when max speed is met

        if path.max_speed_starts[axis_nr] >= path.abs_vec[axis_nr]:
            logging.debug("Max speed is never met")
            sm_start = path.switch[axis_nr]
            sm_end = path.abs_vec[axis_nr]-path.switch[axis_nr]
        else:
            logging.debug("Max speed is met after "+str(path.max_speed_starts[axis_nr])+" meters")
            sm_start = path.max_speed_starts[axis_nr]
            sm_end = path.max_speed_ends[axis_nr]

        s = path.abs_vec[axis_nr]
        a = path.accelerations[axis_nr]
        v_start = path.start_speeds[axis_nr]
        v_end = path.end_speeds[axis_nr]
        
        delays = self.acceleration_profile(stepper, s, a, v_start, v_end, v_max)
        # If the axes are X or Y, we need to transform back in case of 
        # H-belt or some other transform. 
        if axis == "X" or axis == "Y":
            (td_x, td_y) = path.stepper_to_axis(td, axis)
            self.current_pos["X"] += td_x 
            self.current_pos["Y"] += td_y 
        else:                        
            self.current_pos[axis] += td                                    # Update the global position vector
        
        return (step_pins,dir_pins,option_pins, delays)                                           # return the pin states and the data


    def acceleration_profile(stepper, s, a, v_start, v_end, v_max):
        meters_pr_step = 1.0/stepper.get_steps_pr_meter()
        a_idx = np.where(stepper.acc==a)[0][0]
        #distance for start, max, end
        s_start = (v_start**2)/(2.0*a)
        s_max   = (v_max**2)/(2.0*a)
        s_end   = (v_end**2)/(2.0*a)
        # index for start, max, end
        idx_start = int(s_start/meters_pr_step)
        idx_max   = int(s_max/meters_pr_step)
        idx_end   = int(s_end/meters_pr_step)    
        # Make the lookup slices 
        delays_start = np.squeeze(np.asarray(stepper.delays[a_idx, idx_start:idx_max]))
        delays_end   = np.squeeze(np.asarray(stepper.delays[a_idx, idx_end:idx_max]))
        nr_delays_inter = int(s/meters_pr_step)-len(delays_start)-len(delays_end)    
        delays_inter =  np.squeeze(np.asarray(np.ones(nr_delays_inter)*stepper.delays[a_idx, idx_max]))

        # Return the table of delays
        return np.append(np.append(delays_start, delays_inter), np.flipud(delays_end))

    ''' Make the acceleration tables for each of the steppers '''
    def make_acceleration_tables(self):
        for name, stepper in self.steppers.iteritems():
            meters_pr_step = 1.0/stepper.get_steps_pr_meter()
            # Max one meter
            s = 1.0
            num_steps = int(s/meters_pr_step)
            distances = np.cumsum([meters_pr_step]*num_steps)
            acc = np.arange(0.01, 1.01, 0.01)
            a_s = np.matrix(acc).T*distances
            a_o = np.matrix(acc).T*np.ones(len(distances))
            timestamps = (np.sqrt(2.0*a_s))/a_o
            stepper.acc = acc
            stepper.delays = np.diff(timestamps)



if __name__ == '__main__':
    import cProfile
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        pass
    import numpy as np

    from Stepper import Stepper

    print "Making steppers"
    steppers = {}
    steppers["X"] = Stepper("GPIO0_27", "GPIO1_29", "GPIO2_4",  0, "X",None,0,0)
    steppers["X"].set_microstepping(4)
    steppers["Y"] = Stepper("GPIO1_12", "GPIO0_22", "GPIO2_5",  1, "Y",None,1,1)  
    steppers["Y"].set_microstepping(4)
    steppers["Z"] = Stepper("GPIO0_23", "GPIO0_26", "GPIO0_15", 2, "Z",None,2,2)  
    steppers["E"] = Stepper("GPIO1_28", "GPIO1_15", "GPIO2_1",  3, "Ext1",None,3,3)
    steppers["H"] = Stepper("GPIO1_13", "GPIO1_14", "GPIO2_3",  4, "Ext2",None,4,4)

    path_planner = PathPlanner(steppers, None)
    path_planner.make_acceleration_tables()

    radius = 1.0
    speed = 0.1
    acceleration = 0.1
    rand = 0.0

    t = np.arange(0, 1*np.pi/2+(np.pi/10), np.pi/10)
    rand_x = rand*np.random.uniform(-1, 1, size=len(t))
    rand_y = rand*np.random.uniform(-1, 1, size=len(t))

    #for i in t:
    #    path_planner.add_path(Path({"X": radius*np.sin(i)+rand_x[i], "Y": radius*np.cos(i)+rand_y[i]}, speed, Path.ABSOLUTE, acceleration))
    #path_planner.add_path(Path({"X": 0.0, "Y": 0.0}, speed, Path.ABSOLUTE))
    #path_planner.add_path(Path({"X": -0.5, "Y": 0.5}, speed, Path.G92))
    path_planner.add_path(Path({"X": .1, "Y": .1}, speed, Path.RELATIVE, acceleration))
    #path_planner.finalize_paths()

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
        if not path.movement == Path.G92:
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
    delays_x = np.array([])
    delays_y = np.array([])
    for idx, path in enumerate(list(path_planner.paths.queue)):
        path_planner.do_work()
        if not path.movement == Path.G92:
            #plt.arrow(mag_x, path.start_speeds[0], path.abs_vec[0], path.end_speeds[0]-path.start_speeds[0], fc='g', ec='g')
            #plt.arrow(mag_y, 0.5+path.start_speeds[1], path.abs_vec[1], path.end_speeds[1]-path.start_speeds[1], fc='r', ec='r')
            
            # Plot the acceleration profile and deceleration profile
            vec_x = abs(path.vec[0])
            
            print "length: "+str(path.abs_vec[0])
            print "Switch: "+str(path.switch[0])
            s_x = np.arange(0, path.switch[0]*1.01, path.switch[0]*0.01)
            s_xd = np.arange(0, (vec_x-path.switch[0])*1.01, (vec_x-path.switch[0])*0.01)
            #plt.plot(mag_x+s_x,  np.sqrt(np.square(path.start_speeds[0])+ 2*path.accelerations[0]*s_x), 'b')
            #plt.plot(mag_x+s_xd+path.switch[0], 
            #    np.sqrt(np.square(path.start_speeds[0])+ 2*path.accelerations[0]*path.switch[0]) -
            #    2*path.accelerations[0]*s_xd, 'r')

            mag += abs(path.get_magnitude())
            mag_x += path.abs_vec[0]
            mag_y += abs(path.vec[1])
            #if idx == 0:
            delays_x = np.append(delays_x, path.delays[0])
            delays_y = np.append(delays_y, path.delays[1])


    plt.plot(delays_x)
    plt.plot(delays_y)
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
    #plt.xlim([-0.1, mag_x*1.1])
    #plt.ylim([0, 0.02])
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
    

