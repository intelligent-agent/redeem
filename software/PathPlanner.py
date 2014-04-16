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
from Path import Path, AbsolutePath, RelativePath, G92Path
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
            self.pru        = Pru(pru_firmware)
        self.paths          = Queue.Queue(1000)
        self.segments       = []
        self.running        = True
        self.pru_data       = []
        self.t              = Thread(target=self._do_work)
        self.t.daemon       = True
        self.travel_length  = {"X":0.0, "Y":0.0, "Z":0.0}
        self.center_offset  = {"X":0.0, "Y":0.0, "Z":0.0}
        self.acceleration   = 0.1
        self.prev           =  G92Path({"X":0.0, "Y":0.0, "Z":0.0, "E":0.0,"H":0.0}, 0)
        self.prev.set_prev(None)

        if __name__ != '__main__':
            self.t.start()		 

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
        p = RelativePath({axis:-self.travel_length[axis]}, speed)
        self.add_path(p)

        # Reset position to offset
        p = G92Path({axis:-self.center_offset[axis]}, speed)
        self.add_path(p)
        
        # Move to offset
        p = AbsolutePath({axis:0}, speed)
        self.add_path(p)
        self.finalize_paths()
        self.wait_until_done()
        logging.debug("homing done for "+axis)

    ''' Add a path segment to the path planner '''        
    def add_path(self, new):   
        # Link to the previous segment in the chain
        new.set_prev(self.prev)

        if not self.prev.is_added:
            self.segments.append(self.prev)
            self.prev.is_added = True
            # If we find an end segment, add all path segments to the queue for execution           
            if self.prev.is_end_segment:
                logging.debug("Processing all segments on queue!")
                [self.paths.put(path) for path in self.segments]
                self.segments = []

        # If this is a relative move or G92, add it right away
        if new.is_end_segment:
            self.finalize_paths()
            self.paths.put(new)
            new.is_added = True
            self.segments = []

        self.prev = new

    ''' Add the last path to the queue for processing '''
    def finalize_paths(self):
        logging.debug("Finalize paths")
        if self.prev.movement == Path.ABSOLUTE and not self.prev.is_added:
            self.prev.finalize()
            self.segments.append(self.prev)
            self.prev.is_added = True
            [self.paths.put(path) for path in self.segments]
            self.segments = []
    
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
            self.paths.task_done()            
            return                
        
        for axis, val in path.axes.items():                       # Run through all the axes in the path                   
            data = self._make_data(path, axis)        
            if data:
                if len(self.pru_data) == 0:
                    self.pru_data = zip(*data)
                else:
                    #pass
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
        return braid.braid_data_c(data1, data2)               # Use the Optimized C-function for this. 
    
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
        num_steps       = path.num_steps[axis_nr]      # Number of steps to tick
        if num_steps == 0:
            return None
        #logging.debug("Processing "+axis+" of len "+str(path.stepper_vec[axis_nr]))
        step_pin        = stepper.get_step_pin()                            # Get the step pin
        dir_pin         = stepper.get_dir_pin()                             # Get the direction pin
        dir_pin         = 0 if path.stepper_vec[axis_nr] < 0 else dir_pin           # Disable the dir-pin if we are going backwards  
        step_pins       = [step_pin]*num_steps                              # Make the pin states
        dir_pins        = [dir_pin]*num_steps 
        option_pins     = [path.cancellable]*num_steps                  

        #logging.debug(path.profile)

        # Calculate the distance traveled when max speed is met       
        s = path.abs_vec[axis_nr]
        a = path.accelerations[axis_nr]
        d = path.decelerations[axis_nr]
        v_start = path.start_speeds[axis_nr]
        v_end = path.end_speeds[axis_nr]
        v_max = path.max_speeds[axis_nr]
        delays = self.acceleration_profile(stepper, s, a, d, v_start, v_end, v_max)

        if not hasattr(path, 'delays'):
            path.delays = [[], [], [], [], []]
        path.delays[axis_nr] = delays

        return (step_pins,dir_pins,option_pins, delays)                                           # return the pin states and the data

    ''' Make the acceleration profile '''
    def acceleration_profile(self, stepper, s, a, d, v_start, v_end, v_max):
        meters_pr_step = 1.0/stepper.get_steps_pr_meter()
        total_steps = int(np.round(s/meters_pr_step))

        # Generate acceleraion profile 
        if a != 0 and not np.isnan(a):
            abs_a = abs(a)
            ss_accel     = (v_start**2)/(2.0*abs_a)
            se_accel     = (v_max**2)/(2.0*abs_a)
            idx_ss       = int(np.round(ss_accel/meters_pr_step))
            idx_se       = int(np.round(se_accel/meters_pr_step))
            if idx_se < idx_ss:
                idx_se, idx_ss = idx_ss, idx_se
            delays_start = np.diff(np.sqrt(2.0*abs_a*stepper.distances[idx_ss:idx_se+1])/abs_a)
            if a < 0:
                delays_start = np.flipud(delays_start)
        else:
            delays_start = np.array([])

        # Generate deceleration profile
        if d != 0 and not np.isnan(d):
            abs_d = abs(d)
            es_accel     = (v_end**2)/(2.0*abs_d)
            ee_accel     = (v_max**2)/(2.0*abs_d)
            idx_es       = int(np.round(es_accel/meters_pr_step))
            idx_ee       = int(np.round(ee_accel/meters_pr_step))
            if idx_ee < idx_es:
                idx_ee, idx_es = idx_es, idx_ee
            delays_end   = np.diff(np.sqrt(2.0*abs_d*stepper.distances[idx_es:idx_ee+1])/abs_d)                     
            if v_max > v_end:
                delays_end = np.flipud(delays_end)
        else:
            delays_end = np.array([])

        # Generate cruising profile
        nr_delays_inter = total_steps - len(delays_start) - len(delays_end)
        if nr_delays_inter > 0:
            #logging.debug("Cruising "+str(nr_delays_inter))
            delays_inter = np.ones(nr_delays_inter)*(meters_pr_step/v_max)
        else:
            delays_inter = np.array([])

        # Return the table of delays
        return np.append(np.append(delays_start, delays_inter), delays_end)

    ''' Make the acceleration tables for each of the steppers '''
    def make_acceleration_tables(self):
        s = {"X": 1.0, "Y": 1.0, "Z": 0.2, "E": 0.3, "H": 0.3}
        for name, stepper in self.steppers.iteritems():
            meters_pr_step = 1.0/stepper.get_steps_pr_meter()
            num_steps = int(s[name]/meters_pr_step)
            stepper.distances = np.cumsum([meters_pr_step]*num_steps)


    def save_acceleration_tables(self):
        for name, stepper in self.steppers.iteritems():
            np.savetxt('distances_'+name+'.npy', stepper.distances)

    def load_acceleration_tables(self):
        dirname = os.path.dirname(os.path.realpath(__file__))
        for name, stepper in self.steppers.iteritems():
            stepper.distances = np.loadtxt(dirname+'/distances_'+name+'.npy')

if __name__ == '__main__':
    import cProfile
    import numpy as np

    import sys

    logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')


    from Stepper import Stepper
    from Gcode import Gcode


    Path.steps_pr_meter = np.array([24000, 24000, 64000, 20000, 20000])
        
    
    print "Making steppers"
    steppers = {}
    steppers["X"] = Stepper("GPIO0_27", "GPIO1_29", "GPIO2_4",  0, "X",None,0,0)
    steppers["X"].set_microstepping(2)
    steppers["X"].set_steps_pr_mm(6.0)
    steppers["Y"] = Stepper("GPIO1_12", "GPIO0_22", "GPIO2_5",  1, "Y",None,1,1)  
    steppers["Y"].set_microstepping(2)
    steppers["Y"].set_steps_pr_mm(6.0)
    steppers["Z"] = Stepper("GPIO0_23", "GPIO0_26", "GPIO0_15", 2, "Z",None,2,2)  
    steppers["Z"].set_microstepping(2)
    steppers["Z"].set_steps_pr_mm(160.0)
    steppers["E"] = Stepper("GPIO1_28", "GPIO1_15", "GPIO2_1",  3, "Ext1",None,3,3)
    steppers["E"].set_microstepping(2)
    steppers["E"].set_steps_pr_mm(5.0)
    steppers["H"] = Stepper("GPIO1_13", "GPIO1_14", "GPIO2_3",  4, "Ext2",None,4,4)
    steppers["H"].set_microstepping(2)
    steppers["H"].set_steps_pr_mm(5.0)

    path_planner = PathPlanner(steppers, None)
    path_planner.make_acceleration_tables()
    path_planner.save_acceleration_tables()
    path_planner.load_acceleration_tables()
    #Path.axis_config = Path.AXIS_CONFIG_H_BELT


    radius = 0.05
    speed = 0.09
    acceleration = 0.001
    rand = 0.0
    plotfac = 1.5

    ds = np.pi/16
    t = np.arange(-np.pi/4, np.pi/4+ds, ds)
    rand_x = rand*np.random.uniform(-1, 1, size=len(t))
    rand_y = rand*np.random.uniform(-1, 1, size=len(t))
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as infile:         
            for line in infile:
                g = Gcode({"message": line, "prot": None})
                if g.code() == "G1":
                    if g.has_letter("F"):                                    # Get the feed rate                 
                        speed = float(g.get_value_by_letter("F"))/60000.0 # Convert from mm/min to SI unit m/s
                        g.remove_token_by_letter("F")
                    smds = {}
                    for i in range(g.num_tokens()):                          
                        axis = g.token_letter(i)                             
                        smds[axis] = float(g.token_value(i))/1000.0          # Get the value, new position or vector   
                    path_planner.add_path(AbsolutePath(smds, speed, acceleration))
        path_planner.finalize_paths()
    else:
        for idx, i in enumerate(t):
            path_planner.add_path(AbsolutePath(
                {"X": radius*np.sin(i)+rand_x[i], "Y": radius*np.cos(i)+rand_y[i], 
                 "E": 0.01*(idx+1)
                }, speed, acceleration))
            #path_planner.add_path(Path({"X": radius*(16*np.power(np.sin(i), 3)), "Y": radius*(13*np.cos(i)-5*np.cos(2*i)-2*np.cos(3*i)-np.cos(4*i))}, speed, Path.ABSOLUTE, acceleration))
            
        #path_planner.add_path(AbsolutePath({"X": -0.1, "Y": 0.1}, speed, acceleration))
        #path_planner.add_path(AbsolutePath({"X": 0.0, "Y": 0.2}, speed, acceleration))
        #path_planner.add_path(AbsolutePath({"X": 0.1, "Y": 0.1}, speed, acceleration))
        #path_planner.add_path(AbsolutePath({"X": 0.0, "Y": 0.0}, speed, acceleration))
        path_planner.finalize_paths()
        #path_planner.add_path(RelativePath({"X": -radius, "Y": -radius}, speed, acceleration))


    try:
        import matplotlib.pyplot as plt
    except ImportError:
        exit(0)


    ax0 = plt.subplot(2, 3, 4)
    plt.ylim([-plotfac*radius, plotfac*radius])
    plt.xlim([-plotfac*radius, plotfac*radius])
    plt.title('Trajectory')

    print "Trajectory done"
    speeds_x = []
    speeds_y = []
    speeds_e = []
    speeds = []
    magnitudes = []

    for path in list(path_planner.paths.queue):
        if not path.movement == Path.G92:
            print path.vec[:2]
            if (path.vec[:2] != 0).any():
                ax0.arrow(path.start_pos[0], path.start_pos[1], path.vec[0], path.vec[1], 
                    width=0.00001, head_width=0.0005, head_length=0.001, fc='k', ec='k',  length_includes_head=True)
            magnitudes.append(path.get_magnitude())
            speeds_x.append(path.start_speeds[0])
            speeds_y.append(path.start_speeds[1])
            speeds.append(np.linalg.norm(path.start_speeds[0:2]))
            speeds_e.append(path.start_speeds[3])

    positions = np.insert(np.cumsum(magnitudes), 0, 0)
    speeds_x = np.append(speeds_x, path.end_speeds[0])
    speeds_y = np.append(speeds_y, path.end_speeds[1])
    speeds = np.append(speeds, np.linalg.norm(path.end_speeds[0:2]))
    speeds_e = np.append(speeds_e, path.end_speeds[3])

    ax1 = plt.subplot(2, 3, 5)
    plt.plot(positions, speeds_x, "r")
    plt.plot(positions, speeds_y, "b")
    plt.plot(positions, speeds, "g")
    plt.plot(positions, speeds_e, "y")
    plt.ylim([0, np.max(speeds)*1.5])
    plt.xlim([0, positions[-1]*1.1])
    plt.title('Velocity')

    # Acceleration
    ax2 = plt.subplot(2, 3, 6)
    delays = np.array([])
    delays2 = np.array([])
    delays3 = np.array([])
    mag = 0
    mag_x = 0
    mag_y = 0  
    mag_e = 0  
    for idx, path in enumerate(list(path_planner.paths.queue)):
        path_planner.do_work()
        if not path.movement == Path.G92:
            plt.arrow(mag_x, path.start_speeds[0], path.abs_vec[0], path.end_speeds[0]-path.start_speeds[0], fc='r', ec='r', width=0.00001)
            plt.arrow(mag_y, path.start_speeds[1], path.abs_vec[1], path.end_speeds[1]-path.start_speeds[1], fc='b', ec='b', width=0.00001)
            plt.arrow(mag_e, path.start_speeds[3], path.abs_vec[3], path.end_speeds[3]-path.start_speeds[3], fc='y', ec='y', width=0.00001)
            
            # Plot the acceleration profile and deceleration profile
            vec_x = abs(path.vec[0])
            mag += abs(path.get_magnitude())
            mag_x += path.abs_vec[0]
            mag_y += abs(path.vec[1])
            mag_e += abs(path.vec[3])
            if hasattr(path, 'delays'):
                delays = np.append(delays, path.delays[0])
                delays2 = np.append(delays2, path.delays[1])
                delays3 = np.append(delays3, path.delays[3])


    plt.xlim([0, max(mag_x, mag_y)])
    plt.ylim([0, speed])
    plt.title('Also velocity')

    # Plot the delays 
    ax2 = plt.subplot(2, 1, 1)
    plt.plot(delays, 'r')
    plt.plot(delays2, 'b')
    plt.plot(delays3, 'y')
    #plt.ylim([0, 0.1])
    plt.title('Delays')

    print "total distance X = "+str(mag_x)
    print "total distance Y = "+str(mag_y)
    print "total distance E = "+str(mag_e)
    print "total time X = "+str(np.sum(delays))
    print "total time Y = "+str(np.sum(delays2))
    print "total time E = "+str(np.sum(delays3))

    plt.show()
    exit(0)


    print "Profiling speed"
    
    nb = 100
    for x in range(nb):
        path = Path({"Z":x*0.001, "X": np.sin(x*0.1), "Y": np.cos(x*0.1)}, 0.1, Path.ABSOLUTE)
        path_planner.add_path(path)
    path_planner.finalize_paths()

    print "Doing work"
    
    cProfile.run('[path_planner.do_work() for i in range('+str(nb)+')]', sort='time')

    print "Going back"

    path = Path({"Z":0, "X":0, "Y":0}, 0.1, Path.ABSOLUTE)
    path_planner.add_path(path)

    cProfile.run('path_planner.do_work()')

    print "done"

