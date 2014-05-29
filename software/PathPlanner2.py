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
from Path2 import Path, AbsolutePath, RelativePath, G92Path
import numpy as np
from Printer import Printer
from PathPlannerNative import PathPlannerNative

import Queue



class PathPlanner:
    ''' Init the planner '''
    def __init__(self, printer, pru_firmware):
        self.printer        = printer
        self.steppers       = printer.steppers


        self.travel_length  = {"X":0.0, "Y":0.0, "Z":0.0}
        self.center_offset  = {"X":0.0, "Y":0.0, "Z":0.0}
        self.prev           =  G92Path({"X":0.0, "Y":0.0, "Z":0.0, "E":0.0,"H":0.0}, 0)
        self.prev.set_prev(None)
 
        if pru_firmware:
            self.native_planner = PathPlannerNative()

            self.native_planner.initPRU( pru_firmware.get_firmware(0), pru_firmware.get_firmware(1))

            self.native_planner.runThread()

    ''' Get the current pos as a dict '''
    def get_current_pos(self):
        pos = np.zeros(Path.NUM_AXES)
        if self.prev:
            pos = self.prev.end_pos        
        pos2 = {}
        for index, axis in enumerate(Path.AXES):
            pos2[axis] = pos[index]

        return pos2
          
    def force_exit(self):
        self.native_planner.stopThread(True)

    ''' Home the given axis using endstops (min) '''
    def home(self,axis):
        return 

        if axis=="E" or axis=="H":
            return

        logging.debug("homing "+axis)
        speed = Path.home_speed[Path.axis_to_index(axis)]
        # Move until endstop is hit
        p = RelativePath({axis:-self.travel_length[axis]}, speed, self.printer.acceleration)
        self.add_path(p)

        # Reset position to offset
        p = G92Path({axis:-self.center_offset[axis]}, speed)
        self.add_path(p)
        
        # Move to offset
        p = AbsolutePath({axis:0}, speed, self.printer.acceleration)
        self.add_path(p)
        self.finalize_paths()
        self.wait_until_done()
        logging.debug("homing done for "+axis)

    ''' Add a path segment to the path planner '''        
    def add_path(self, new):   
        #logging.debug("Adding path "+str(new.movement))
        # Link to the previous segment in the chain
        new.set_prev(self.prev)

        if new.is_G92():
            pass #FIXME: Flush the path in the planner or tell the planner it's a G92....

        #push this new segment
        #unit for speed is mm/min
        #unit for position is in steps
        #FIXME: CLEAN THAT MESS!

        speed = new.speed*60000.0
        start = new.start_pos * Path.steps_pr_meter
        end = new.end_pos * Path.steps_pr_meter

        self.native_planner.queueMove((start[0],start[1],start[2],start[3]),(end[0],end[1],end[2],end[3]),speed)


        self.prev = new

    



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

    printer = Printer()

    printer.steppers = steppers

    path_planner = PathPlanner(printer, None)
    path_planner.make_acceleration_tables()
    #path_planner.save_acceleration_tables()
    #path_planner.load_acceleration_tables()
    #Path.axis_config = Path.AXIS_CONFIG_H_BELT


    radius = 0.05
    speed = 0.1
    acceleration = 0.3
    rand = 0.0
    plotfac = 1.5
    plotoffset_x = 0.1
    plotoffset_y = 0.1

    ds = np.pi/16
    t = np.arange(-np.pi/4, np.pi/4+ds, ds)
    rand_x = rand*np.random.uniform(-1, 1, size=len(t))
    rand_y = rand*np.random.uniform(-1, 1, size=len(t))
    if len(sys.argv) > 1:
        line_nr = 0
        with open(sys.argv[1]) as infile:         
            for line in infile:
                line_nr += 1
                if len(sys.argv) > 3 and line_nr >= int(sys.argv[2]) and line_nr < int(sys.argv[3]):
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
                    elif g.code() == "G92":
                        if g.num_tokens() == 0:
                            logging.debug("Adding all to G92")
                            g.set_tokens(["X0", "Y0", "Z0", "E0", "H0"])            # If no token is present, do this for all
                        pos = {}                                                    # All steppers 
                        for i in range(g.num_tokens()):                             # Run through all tokens
                            axis = g.token_letter(i)                                # Get the axis, X, Y, Z or E
                            pos[axis] = float(g.token_value(i))/1000.0              # Get the value, new position or vector             
                        path = G92Path(pos, speed)                     # Make a path segment from the axes
                        path_planner.add_path(path)  
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
    plt.ylim([-plotfac*radius+plotoffset_y, plotfac*radius+plotoffset_y])
    plt.xlim([-plotfac*radius+plotoffset_x, plotfac*radius+plotoffset_x])
    plt.title('Trajectory')

    print "Trajectory done"
    speeds_x = []
    speeds_y = []
    speeds_e = []
    speeds = []
    magnitudes = []

    for path in list(path_planner.paths.queue):
        if not path.movement == Path.G92:
            #print path.vec[:2]
            if (path.vec[:2] != 0).any():
                ax0.arrow(path.start_pos[0], path.start_pos[1], path.true_vec[0], path.true_vec[1], 
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

    print np.array(magnitudes)
    print speeds
    print speeds_e

    # Acceleration
    ax2 = plt.subplot(2, 3, 6)
    delays = np.array([])
    delays2 = np.array([])
    delays3 = np.array([])
    mag = 0
    mag_x = 0
    mag_y = 0  
    mag_e = 0  
    
    delaysarrow=[]

    for idx, path in enumerate(list(path_planner.paths.queue)):
        path_planner.do_work()
        if not path.movement == Path.G92:
            if hasattr(path, 'delays_pru'):
                delaysarrow.append(np.sum(path.delays_pru))

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
    # plt.plot(np.cumsum(delays),delays, 'r')
    # plt.plot(np.cumsum(delays2),delays2, 'b')
    # plt.plot(np.cumsum(delays3),delays3, 'y')
    # plt.ylim([0, 0.08])

    plt.plot(np.cumsum(path_planner.debug),path_planner.debug, '-r+')
    plt.plot(np.cumsum(path_planner.debug_axis[0]),path_planner.debug_axis[0], '-g+')
    plt.plot(np.cumsum(path_planner.debug_axis[1]),path_planner.debug_axis[1], '-b+')
    deb = 0
    scale=20e5
    for d in delaysarrow:
        plt.arrow(deb,scale, d,0,  width=0.00001*scale, head_width=0.05*scale, head_length=0.1*scale, fc='k', ec='k',  length_includes_head=True)
        deb+=d

 
    plt.title('Delays for X and Y sent to PRU. Black are the path segments.')

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

