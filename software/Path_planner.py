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
import numpy as np  
from threading import Thread
from Pru import Pru

class Path_planner:
    ''' Init the planner '''
    def __init__(self, steppers):
        self.steppers    = steppers
        self.pru         = Pru()                                # Make the PRU
        self.paths       = list()                               # Make a list of paths
        self.current_pos = {"X":0.0, "Y":0.0, "Z":0.0, "E":0.0} # Current position in (x, y, z, e)
        self.running     = True                                 # Yes, we are running
        self.t           = Thread(target=self._do_work)         # Make the thread
        self.t.start()		                

    ''' Set the acceleration used '''
    def set_acceleration(self, acceleration):
        self.acceleration = acceleration

    ''' Add a path segment to the path planner '''        
    def add_path(self, new):        
        self.paths.append(new)
        if len(self.paths) > 1:
            prev = self.paths[0]
            new.set_prev(prev)
            prev.set_next(new)
        
    ''' Return the number of paths currently on queue '''
    def nr_of_paths(self):
        return len(self.paths)

    ''' Join the thread '''
    def exit(self):
        self.running = False
        self.t.join()

    def set_pos(self, axis, pos):
        self.current_pos[axis] = pos
    
    def get_pos(self, axis):
        return self.current_pos[axis]

    def reset_pos(self):
        self.current_pos = {"X":0.0, "Y":0.0, "Z":0.0, "E":0.0}
        print "Path planner: pos reset"
    
    ''' Add a certain length to a vector '''
    def add_to_pos(axis, vec):
        self.current_pos[axis] += vec

    ''' This loop pops a path, sends it to the PRU 
    and waits for an event '''
    def _do_work(self):
        events_waiting = 0
        while self.running:
            if len(self.paths) > 0:
                path = self.paths.pop(0)                            # Get the last path added
                path.set_global_pos(self.current_pos.copy())               # Set the global position of the printer
                axes_added = 0
                all_data = {}
                slowest =  0
                for axis in path.get_axes():                        # Run through all the axes in the path    
                    stepper = self.steppers[axis]                   # Get a handle of  the stepper                    
                    data = self._make_data(path, axis)
                    if len(data[0]) > 0:
                        all_data[axis] = data                       # Generate the timing and pin data                         
                        slowest = max(slowest, sum(data[1]))   

                for axis in all_data:                         
                    packet = all_data[axis]                           
                    delays = np.array(packet[1])
                    diff = (slowest-sum(delays))/len(delays)
                    for j, delay in enumerate(delays):
                        delays[j] = max(delay+diff, 2.0/1000.0)   # min 2ms                     
                    data = (packet[0], delays)                    
                    while not self.pru.has_capacity_for(len(delays)*2):# Wait until the PRU has capacity for this chunk of data
                        time.sleep(0.1)
                    axes_added += self.pru.add_data(data)
                    

                if axes_added > 0:
                    self.pru.commit_data()                             # Commit data to ddr 
                    events_waiting += 1
                    if events_waiting > 20:
                        self.pru.wait_for_event(True)                       # Wait for the PRU to finish execution 
                        events_waiting -= 1
                '''
                for axis in all_data: 
                    packet = all_data[axis]                           
                    delays = np.array(packet[1])
                    diff = (slowest-sum(delays))/len(delays)
                    for j, delay in enumerate(delays):
                        delays[j] = max(delay+diff, 2.0/1000)                     
                    data = (packet[0], delays)                    
                    self.steppers[axis].add_data(data)

                for axis in all_data:                            
                    self.steppers[axis].prepare_move()
                for axis in all_data:                            
                    self.steppers[axis].start_move()
                for axis in all_data:                            
                    self.steppers[axis].end_move()
               '''
               
            elif events_waiting > 1:
                 self.pru.wait_for_event(True)                       # Wait for the PRU to finish execution
                 events_waiting -= 1   
            else:
                time.sleep(0.1)                                     # If there is no paths to execute, sleep. 

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
        ratio       = path.get_axis_ratio(axis)

        Vm = path.get_max_speed()*ratio				                    # The travelling speed in m/s
        a  = self.acceleration*ratio    		                        # Accelleration in m/s/s
        ds = 1.0/steps_pr_meter                                         # Delta S, distance in meters travelled pr step. 
        u  = ratio*path.get_min_speed()                 	            # Minimum speed in m/s
        tm = (Vm-u)/a					                                # Calculate the time for when max speed is met. 
        sm = min(u*tm + 0.5*a*tm*tm, s/2.0)			                    # Calculate the distance traveled when max speed is met

        distances       = list(np.arange(0, sm, ds))		            # Table of distances                       
        timestamps      = [(-u+np.sqrt(2.0*a*ss+u*u))/a for ss in distances]# Make a table of times when a tick occurs   
        delays          = np.diff(timestamps)/2.0			                # We are more interested in the delays pr second.         
        delays = list(np.array([delays, delays]).transpose().flatten()) # Double the array so we have timings for up and down  
  
        i_steps     = num_steps-len(delays)		                        # Find out how many delays are missing
        i_delays    = [(ds/Vm)/2.0]*i_steps*2		                    # Make the intermediate steps
        delays      += i_delays+delays[::-1]                            # Add the missing delays. These are max_speed
        td          = num_steps/steps_pr_meter                          # Calculate the actual travelled distance        
        if vec < 0:                                                     # If the vector is negative, negate it.      
            td     *= -1.0

        path.set_travelled_distance(axis, td)                           # Set the travelled distance back in the path 
        self.current_pos[axis] += td                                    # Update the global position vector

        return (pins, delays)                                           # return the pin states and the data




