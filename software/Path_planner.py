'''
Path planner for Replicape. Just add paths to 
this and they will be executed as soon as no other 
paths are being executed. 
It's a good idea to stack up maybe five path 
segments, to have a buffer. 

Author: Elias Bakken
email: elias.bakken@gmail.com
Website: http://www.hipstercircuits.com
License: BSD

You can use and change this, but keep this heading :)
'''

import time
import logging
import numpy as np  
from threading import Thread
from Pru import Pru
import Queue
from collections import defaultdict

class Path_planner:
    ''' Init the planner '''
    def __init__(self, steppers, current_pos):
        self.steppers    = steppers
        self.pru         = Pru()                                # Make the PRU
        self.paths       = Queue.Queue(30)                      # Make a queue of paths
        self.current_pos = current_pos                          # Current position in (x, y, z, e)
        self.running     = True                                 # Yes, we are running
        self.pru_data    = defaultdict(int)
        self.t           = Thread(target=self._do_work)         # Make the thread
        self.t.start()		                

    ''' Set the acceleration used ''' # Fix me, move this to path
    def set_acceleration(self, acceleration):
        self.acceleration = acceleration

    ''' Add a path segment to the path planner '''        
    def add_path(self, new):        
        self.paths.put(new)
        if hasattr(self, 'prev'):
            self.prev.set_next(new)
            new.set_prev(self.prev)
        self.prev = new        
        
    ''' Return the number of paths currently on queue '''
    def nr_of_paths(self):
        return self.paths.qsize()

    ''' Set position for an axis '''
    def set_pos(self, axis, val):
        self.current_pos[axis] = val
	
    def wait_until_done(self):
        '''Wait until planner is done'''
        self.paths.join()
        self.pru.wait_until_done()		 

    ''' This loop pops a path, sends it to the PRU 
    and waits for an event '''
    def _do_work(self):
        while self.running:       
            try: 
                path = self.paths.get(timeout = 1)                            # Get the last path added
                path.set_global_pos(self.current_pos.copy())       # Set the global position of the printer
                all_data = {}
                slowest =  0
                for axis in path.get_axes():                       # Run through all the axes in the path    
                    stepper = self.steppers[axis]                  # Get a handle of  the stepper                    
                    data = self._make_data(path, axis)
                    if len(data[0]) > 0:
                        all_data[axis] = data                      # Generate the timing and pin data                         
                        slowest = max(slowest, sum(data[1]))                                   
                
                for axis in all_data:                              # Make all axes use the same amount of time
                    packet = all_data[axis]                           
                    delays = np.array(packet[1])
                    diff = (slowest-sum(delays))/len(delays)
                    for j, delay in enumerate(delays):
                        delays[j] = max(delay+diff, 1.0/10000.0)    # min 0.1ms                     
                    data = (packet[0], delays)                  
              
                for axis in all_data:                               # Merge the data from all axes   
                    packet = all_data[axis]
                    z = zip(np.cumsum(packet[1]), packet[0])
                    for item in z:
                        self.pru_data[item[0]] += item[1]

                if len(self.pru_data) > 0:
                    z = zip(*sorted(self.pru_data.items()))
                    self.pru_data = (list(z[1]), list(np.diff([0]+list(z[0]))))
                    while not self.pru.has_capacity_for(len(self.pru_data[0])*8):
                        time.sleep(1)              
         
                    self.pru.add_data(self.pru_data)
                    self.pru.commit_data()                            # Commit data to ddr

                self.pru_data = defaultdict(int)                    
                self.paths.task_done()
               
            except Queue.Empty:
                pass

    ''' Join the thread '''
    def exit(self):
        self.running = False
        self.pru.join()
        logging.debug("pru joined")
        self.t.join()
        logging.debug("path planner joined")


    ''' Make the data for the PRU or steppers '''
    def _make_data(self, path, axis):     
        stepper         = self.steppers[axis]
        steps_pr_meter  = stepper.get_steps_pr_meter()
        vec             = path.get_axis_length(axis)                        # Total travel distance
        num_steps       = int(abs(vec) * steps_pr_meter)                    # Number of steps to tick
        if num_steps == 0:
            return ([], [])
        step_pin    = stepper.get_step_pin()                            # Get the step pin
        dir_pin     = stepper.get_dir_pin()                             # Get the direction pin
        dir_pin     = 0 if vec < 0 else dir_pin                         # Disable the dir-pin if we are going backwards               
        pins        = [step_pin | dir_pin, dir_pin]*num_steps           # Make the pin states

        s           = abs(path.get_axis_length(axis))                   # Get the length of the vector
        ratio       = path.get_axis_ratio(axis)                         # Ratio is the length of this axis to the total length

        Vm       = path.get_max_speed()*ratio				            # The travelling speed in m/s
        a        = self.acceleration*ratio    		                    # Accelleration in m/s/s
        ds       = 1.0/steps_pr_meter                                   # Delta S, distance in meters travelled pr step.         
        if self.pru.is_processing():                                    # If there is currently a segment being processed, 
            #print "Is processing, angle to prev is "+str(path.angle_to_prev())
            u_start  = ratio*path.get_start_speed()                 	    # The end speed, depends on the angle to the next
        else:
            #print "Nothing processing"
            u_start = 0
        if self.paths.qsize() > 0:                                      # If there are paths in queue, we do not have to slow down
            #print "Has followers, angle to follower: "+str(path.angle_to_next()) 
            u_end    = ratio*path.get_end_speed()                 	    # The start speed. Depends on the angle to the prev.
        else:
            #print "Nothing on queue"
            u_end = 0

        #print "Max speed for "+axis+" is "+str(Vm)
        #print "Start speed for "+axis+" is "+str(u_start)
        #print "End speed for "+axis+" is "+str(u_end)
        #print ""
        tm_start = (Vm-u_start)/a					                    # Calculate the time for when max speed is met. 
        tm_end   = (Vm-u_end)/a					                        # Calculate the time for when max speed is met. 
        sm_start = min(u_start*tm_start + 0.5*a*tm_start**2, s/2.0)     # Calculate the distance traveled when max speed is met
        sm_end   = min(u_end*tm_end + 0.5*a*tm_end**2, s/2.0)           # Calculate the distance traveled when max speed is met

        distances_start  = list(np.arange(0, sm_start, ds))		        # Table of distances                       
        distances_end    = list(np.arange(0, sm_end, ds))		        # Table of distances                       
        timestamps_start = [(-u_start+np.sqrt(2.0*a*ss+u_start**2))/a for ss in distances_start]# When ticks occur
        timestamps_end   = [(-u_end  +np.sqrt(2.0*a*ss+u_end**2))/a for ss in distances_end]# When ticks occur
        delays_start     = np.diff(timestamps_start)/2.0			         # We are more interested in the delays pr second. 
        delays_end       = np.diff(timestamps_end)/2.0			         # We are more interested in the delays pr second.         
        delays_start     = list(np.array([delays_start, delays_start]).transpose().flatten())         
        delays_end       = list(np.array([delays_end, delays_end]).transpose().flatten()) 

        i_steps     = 2*num_steps-len(delays_start)-len(delays_end)       # Find out how many delays are missing
        i_delays    = [(ds/Vm)/2.0]*i_steps  		                    # Make the intermediate steps
        delays      = delays_start+i_delays+delays_end[::-1]                  # Add the missing delays. These are max_speed
        td          = num_steps/steps_pr_meter                          # Calculate the actual travelled distance        
        if vec < 0:                                                     # If the vector is negative, negate it.      
            td     *= -1.0
        self.current_pos[axis] += td                                    # Update the global position vector

        return (pins, delays)                                           # return the pin states and the data


