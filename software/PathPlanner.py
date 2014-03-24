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


import Queue
from collections import defaultdict
import braid

class PathPlanner:
    ''' Init the planner '''
    def __init__(self, steppers, pru_firmware):
        self.steppers    = steppers
        self.pru         = Pru(pru_firmware)                 # Make the PRU
        self.paths       = Queue.Queue(10)                      # Make a queue of paths
        self.current_pos = {"X":0.0, "Y":0.0, "Z":0.0, "E":0.0,"H":0.0}
        self.running     = True                                 # Yes, we are running
        self.pru_data    = []
        self.t           = Thread(target=self._do_work)         # Make the thread
        self.t.daemon    = True
        self.travel_length = {"X":0.0, "Y":0.0, "Z":0.0}
        self.center_offset = {"X":0.0, "Y":0.0, "Z":0.0}

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
        if not new.is_G92():     
            if hasattr(self, 'prev'):
                self.prev.set_next(new)
                new.set_prev(self.prev)
            self.prev = new        
        self.paths.put(new)

    ''' Return the number of paths currently on queue '''
    def nr_of_paths(self):
        return self.paths.qsize()

    ''' Set position for an axis '''
    def _set_pos(self, axis, val):
        self.current_pos[axis] = val

    def wait_until_done(self):
        '''Wait until planner is done'''
        self.paths.join()
        self.pru.wait_until_done()		 

    def _do_work(self):
        """ This loop pops a path, sends it to the PRU and waits for an event """
        while self.running:       
           self.do_work()
    
    def do_work(self):
        """ This is just a separate function so the test at the bottom will pass """		
        path = self.paths.get()                            # Get the last path added
        path.set_global_pos(self.current_pos.copy())       # Set the global position of the printer

        if path.is_G92():                                   # Only set the position of the axes
            for axis, pos in path.get_pos().iteritems():                       # Run through all the axes in the path    
                self._set_pos(axis, pos)           
            self.paths.task_done()            
            return                
        
        for axis in path.get_axes():                       # Run through all the axes in the path                   
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
                #logging.debug("Pru full")              
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
        num_steps       = int(abs(path.vec[axis_nr]) * steps_pr_meter)      # Number of steps to tick
        if num_steps == 0:
            return ([], [])
        step_pin        = stepper.get_step_pin()                            # Get the step pin
        dir_pin         = stepper.get_dir_pin()                             # Get the direction pin
        dir_pin         = 0 if vec < 0 else dir_pin                         # Disable the dir-pin if we are going backwards  
        step_pins       = [step_pin]*num_steps                              # Make the pin states
        dir_pins        = [dir_pin]*num_steps 
        option_pins     = [path.cancellable]*num_steps                  

        s           = abs(path.vec[axis_nr])                    
        ratio       = path.get_axis_ratio(axis_nr)                      # Ratio is the length of this axis to the total length

        Vm       = path.speed*ratio				                        # The travelling speed in m/s
        a        = path.acceleration*ratio    		                    # Accelleration in m/s/s
        ds       = 1.0/steps_pr_meter                                   # Delta S, distance in meters travelled pr step.         
        
        u_start  = ratio*path.get_start_speed()                 	    # The end speed, depends on the angle to the next
        u_end    = ratio*path.get_end_speed()                 	        # The start speed. Depends on the angle to the prev.

        logging.debug('Start speed '+str(path.get_start_speed()))
        logging.debug('End speed '+str(path.get_end_speed()))

        tm_start = (Vm-u_start)/a					                    # Calculate the time for when max speed is met. 
        tm_end   = (Vm-u_end)/a					                        # Calculate the time for when max speed is met. 
        sm_start = min(u_start*tm_start + 0.5*a*tm_start**2, s/2.0)     # Calculate the distance traveled when max speed is met
        sm_end   = min(u_end*tm_end + 0.5*a*tm_end**2, s/2.0)           # Calculate the distance traveled when max speed is met

        distances_start  = np.arange(0, sm_start, ds)		            # Table of distances                     
        distances_end    = np.arange(0, sm_end, ds)		                # Table of distances     

        timestamps_start = (-u_start+np.sqrt(2.0*a*distances_start+u_start**2))/a    # When ticks occur
        timestamps_end   = (-u_end  +np.sqrt(2.0*a*distances_end+u_end**2))/a        # When ticks occur

        delays_start     = np.diff(timestamps_start)/2.0			    # We are more interested in the delays pr second. 
        delays_end       = np.diff(timestamps_end)/2.0			        # We are more interested in the delays pr second.         
        #delays_start     = np.array([delays_start, delays_start]).transpose().flatten()
        #delays_end       = np.array([delays_end, delays_end]).transpose().flatten()

        i_steps     = num_steps-len(delays_start)-len(delays_end)     # Find out how many delays are missing
        i_delays    = [(ds/Vm)/2.0]*i_steps  		                    # Make the intermediate steps
        delays      = np.concatenate([delays_start, i_delays, np.flipud(delays_end)])# Add the missing delays. 
        td          = num_steps/steps_pr_meter                          # Calculate the actual travelled distance        
        if vec < 0:                                                     # If the vector is negative, negate it.      
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
    from Stepper import Stepper
    from Path import Path
    import cProfile
    import ConfigParser

    logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')

    print "Making steppers"
    steppers = {}
    steppers["X"] = Stepper("GPIO0_27", "GPIO1_29", "GPIO2_4",  0, "X",-1,None,0,0) 
    steppers["Y"] = Stepper("GPIO1_12", "GPIO0_22", "GPIO2_5",  1, "Y",1,None,1,1)  
    steppers["Z"] = Stepper("GPIO0_23", "GPIO0_26", "GPIO0_15", 2, "Z",1,None,2,2)  
    steppers["E"] = Stepper("GPIO1_28", "GPIO1_15", "GPIO2_1",  3, "Ext1",-1,None,3,3)
    steppers["H"] = Stepper("GPIO1_13", "GPIO1_14", "GPIO2_3",  4, "Ext2",-1,None,4,4)
    config = ConfigParser.ConfigParser()
    config.readfp(open('config/default.cfg'))

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
    

