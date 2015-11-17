#!/usr/bin/env python
"""
A filament sensor is a class of sensors that either 
detect the presence of filament, measures filament travel distance 
or filament diameter. For now, only filament distance 
is implemented. The idea is that the filament sensor can 
gather data from various sources and make decisions based 
on the data it gathers. 

Author: Elias Bakken

 Redeem is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Redeem is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Redeem.  If not, see <http://www.gnu.org/licenses/>.
"""
from threading import Thread
import time
import logging
from Redeem import printer

class FilamentSensor:

    def __init__(self):
        self.alarm_level = []
        self.current_pos = []
        self.ideal_pos = []
        self.error_pos = []
        self.sensors = []
        self.t = Thread(target=self._loop)
        self.running = True
        self.t.start()

    def set_alarm_level(self, level, ext_num=0):
        ''' Set the distance error for which to sound an alarm '''
        self.alarm_level[ext_num] = level

    def add_sensor(self, sensor):
        ''' Add a sensor to monitor '''
        self.current_pos.append(0)
        self.ideal_pos.append(0)
        self.error_pos.append(0)
        self.alarm_level.append(0)
        self.sensors.append(sensor)
        
    def set_ideal_position(self, pos, ext_num=0):
        ''' Sets the position the extruder should have travelled. '''
        self.ideal_pos[ext_num] = pos

    def get_diff(self, ext_num=0):
        ''' Return the error in position '''
        return self.error[ext_num]

    def alarm(self, ext_num):
        logging.warning("Extruder {} has reported too large deviation".fomat(ext_num))

    def _loop(self):
        ''' Gather distance travelled from each of the sensors '''
        while self.running:
            for i, sensor in enumerate(self.sensors):
                self.current_pos[i] = sensor.get_distance()
                self.error_pos[i] = self.current_pos[i]-self.ideal_pos[i]
                if printer:
                    self.ideal_pos[i] = printer.path_planner.get_extruder_pos(i)
                logging.debug("Error :"+str(self.error_pos[0]))
                print("Error :"+str(self.error_pos[0]))
                if self.error_pos[i] > self.alarm_level[i]: 
                    self.alarm(i)
            time.sleep(1)

    def stop(self):
        self.running = False
        self.t.join()



if __name__ == '__main__':
    from RotaryEncoder import *
    r = RotaryEncoder("/dev/input/event1", 360, 3)
    f = FilamentSensor()
    f.add_sensor(r)
    f.set_alarm_level(1, 0)
    time.sleep(10)
    r.stop()
    f.stop()



