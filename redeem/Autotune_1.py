"""
Autotune for Redeem

Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: GNU GPL v3: http://www.gnu.org/copyleft/gpl.html

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

from __future__ import division, print_function
import time
import logging
import numpy as np
from threading import Thread
try:
    from Gcode import Gcode
    from Util import Util
except ImportError:
    from redeem.Gcode import Gcode
    from redeem.Util import Util

class Autotune_1:

    def __init__(self, heater, temp=200.0, cycles=4, g=None, printer=None):        
        self.heater                 = heater
        self.steady_temperature     = temp        # Steady state starting temperture
        self.cycles                 = cycles
        self.g                      = g
        self.printer                = printer
        self.output_step            = 10.0        # Degrees to step
        self.E                      = 1.0         # Hysteresis
        self.tuning_algorithm       = "TL"        # Ziegler-Nichols

        self.plot_temps = []

    def cancel(self):
        self.running = False

    def send_temperatures(self):
        while self.running:
            m105 = Gcode({"message": "M105", "prot": self.g.prot})
            self.printer.processor.execute(m105)
            answer = m105.get_answer()
            m105.set_answer(answer[2:])  # strip away the "ok"
            self.printer.reply(m105)
            self.plot_temps.append("({}, {:10.4f})".format(time.time(), self.heater.get_temperature_raw() ))
            time.sleep(1)
        logging.debug(self.plot_temps)

    def run(self):
        """ Start the PID autotune loop """
        # Reset found peaks
        self.running = True

        # Start sending thread
        self.t = Thread(target=self.send_temperatures)
        self.t.start()

        # Enable on-off control
        self.has_onoff_control = self.heater.onoff_control
        self.heater.onoff_control = True

        # Set the standard parameters
        self.d = self.bias = 0.5
        self.heater.max_power = 1.0

        # Start stepping temperatures
        logging.debug("Starting cycles")
        self._tune()
        #logging.debug("Tuning data: "+str(self.temps))

        # Set the new PID settings
        self.heater.Kp = self.Kp
        self.heater.Ti = self.Ti
        self.heater.Td = self.Td

        # Clean shit up
        self.heater.onoff_control = self.has_onoff_control
        self.running = False
        self.t.join()


    def _tune(self):
        self.temps = np.array([])
        self.times = np.array([])
        for cycle in range(self.cycles):
            logging.debug("Doing cycle: "+str(cycle))


            # Turn on heater and wait until temp>setpoint
            self.t_high = time.time()
            self.heater.set_target_temperature(self.steady_temperature + self.output_step)
            while self.heater.get_temperature_raw() < self.steady_temperature + self.E:
                self.temps = np.append(self.temps, self.heater.get_temperature_raw())
                time.sleep(0.01)
            self.t_high = time.time() - self.t_high

            # Turn off heater and wait until temp<setpoint 
            self.t_low = time.time()
            self.heater.set_target_temperature(self.steady_temperature - self.output_step)
            while self.heater.get_temperature_raw() > self.steady_temperature - self.E:
                self.temps = np.append(self.temps, self.heater.get_temperature_raw())
                time.sleep(0.01)
            self.t_low = time.time() - self.t_low

            if cycle > 0:
                logging.debug("th: {}, tl: {}".format(self.t_low, self.t_high))
                self.bias += (self.d*(self.t_high - self.t_low))/(self.t_low + self.t_high);
                self.bias = np.clip(self.bias, 0.1 , 0.9)
                self.d = 1.0 - self.bias if self.bias > 0.5 else self.bias

                if cycle > 2:
                    logging.debug("Smoothing")
                    self.smooth_temps = Util.smooth(self.temps, 1000)
                    self.smooth_temps = self.smooth_temps[:-1000] # Remove window length
                    self.peaks = Util.detect_peaks(self.smooth_temps)
                    self.valleys = Util.detect_peaks(self.smooth_temps, valley=True)
                    logging.debug("peaks: "+str(self.peaks))
                    logging.debug("valls: "+str(self.valleys))
                    logging.debug("temps len: "+str(len(self.temps))+" "+str(len(self.smooth_temps)))
                    
                    self.max_temp = self.temps[self.peaks[-1]]
                    self.min_temp = self.temps[self.valleys[-1]]
                    logging.debug("Max: "+str(self.max_temp))
                    logging.debug("Min: "+str(self.min_temp))
                
                    # Calculate amplitude response
                    #a_single=(abs_max-abs_min)/2.0
                    #d_single=(self.high_cycle_power)/2.0

                    # Calculate the ultimate gain 
                    #Ku=(4.0/np.pi) * (self.d / np.sqrt(a_single**2 + self.E**2))

                    a = self.max_temp-self.min_temp
                    self.Ku = (4.0 * self.d) / (np.pi * np.sqrt(a**2 + self.E**2))
                    self.Pu = self.t_low + self.t_high


                    # (13) Geometric mean 
                    #d_single = np.sqrt((self.setpoint_power-0)*(self.high_cycle_power-self.setpoint_power))

                    # Calculate the oscillation period of the peaks
                    #Pu = (times[peaks[-2]]-times[peaks[-3]])



                    # Tyreus-Luyben: 
                    if self.tuning_algorithm == "TL":
                        self.Kp = 0.45*self.Ku
                        self.Ti = 2.2*self.Pu
                        self.Td = self.Pu/6.3

                    # Classic Zieger-Nichols 
                    elif self.tuning_algorithm == "ZN":
                        self.Kp = 0.6*self.Ku
                        self.Ti = self.Pu/2.0
                        self.Td = self.Pu/8.0

                    print("Temperature diff: "+str(a)+" deg. C")
                    print("Oscillation period: "+str(self.Pu)+" seconds")
                    print("Ultimate gain: "+str(self.Ku))
                    print("Kp: "+str(self.Kp))
                    print("Ti: "+str(self.Ti))
                    print("Td: "+str(self.Td))

            self.heater.max_power = self.bias + self.d
            logging.debug("Power set to "+str(self.heater.max_power))

        logging.debug("Cycles completed")
        self.heater.set_target_temperature(0)
        self.heater.max_power = 1.0

if __name__ == "__main__":
    import matplotlib.pyplot as plt

    data = [(1464045226.1,    93.8263), (1464045227.12,    93.6712), (1464045228.12,    93.4540), (1464045229.14,    93.3919), (1464045230.15,    93.2677), (1464045231.16,    93.3298), (1464045232.17,    93.4540), (1464045233.18,    93.6712), (1464045234.2,    93.9194), (1464045235.21,    94.2916), (1464045236.22,    94.7257), (1464045237.22,    95.3146), (1464045238.24,    95.8725), (1464045239.25,    96.5235), (1464045240.26,    97.2366), (1464045241.27,    98.0122), (1464045242.28,    98.9129), (1464045243.28,    99.7837), (1464045244.3,   100.6250), (1464045245.31,   101.6243), (1464045246.32,   102.5326), (1464045247.32,   103.5381), (1464045248.33,   104.4844), (1464045249.35,   105.5616), (1464045250.36,   106.5487), (1464045251.37,   107.6053), (1464045252.38,   108.7007), (1464045253.4,   109.8036), (1464045254.41,   110.9149), (1464045255.42,   111.9690), (1464045256.43,   113.0985), (1464045257.44,   114.2048), (1464045258.45,   115.3217), (1464045259.46,   116.4500), (1464045260.47,   117.5210), (1464045261.49,   118.6738), (1464045262.5,   119.9116), (1464045263.51,   120.9858), (1464045264.53,   122.0730), (1464045265.54,   123.3589), (1464045266.55,   124.4020), (1464045267.57,   125.5346), (1464045268.58,   126.7223), (1464045269.59,   127.9286), (1464045270.61,   128.9556), (1464045271.61,   130.1588), (1464045272.63,   131.3826), (1464045273.63,   132.5864), (1464045274.65,   133.6415), (1464045275.66,   134.7567), (1464045276.68,   135.8472), (1464045277.69,   137.0460), (1464045278.71,   138.1309), (1464045279.72,   139.2814), (1464045280.73,   140.4539), (1464045281.74,   141.5048), (1464045282.75,   142.5744), (1464045283.76,   143.7138), (1464045284.77,   144.8759), (1464045285.79,   145.9059), (1464045286.8,   147.0077), (1464045287.81,   148.1316), (1464045288.82,   149.1682), (1464045289.83,   150.1685), (1464045290.84,   151.4165), 
(1464045291.85,   152.4009), (1464045292.87,   153.4631), (1464045293.88,   154.5468), (1464045294.89,   155.5291), (1464045295.9,   156.6565), (1464045296.91,   157.6148), (1464045297.92,   158.5255), (1464045298.93,   159.7203), (1464045299.94,   160.7377), (1464045300.95,   161.7757), (1464045301.96,   162.8352), (1464045302.98,   163.7717), (1464045303.98,   164.8744), (1464045304.99,   165.7742), (1464045306.01,   166.6905), (1464045307.02,   167.7813), (1464045308.04,   168.8160), (1464045309.05,   169.7906), (1464045310.06,   170.7849), (1464045311.08,   171.6291), (1464045312.09,   172.6616), (1464045313.1,   173.6276), (1464045314.11,   174.6130), (1464045315.13,   175.5265), (1464045316.15,   176.4574), (1464045317.17,   177.6949), (1464045318.19,   178.2769), (1464045319.2,   179.2627), (1464045320.21,   180.4728), (1464045321.21,   181.1929), (1464045322.22,   182.2407), (1464045323.24,   183.0957), (1464045324.25,   184.0761), (1464045325.26,   185.0768), (1464045326.28,   186.0989), (1464045327.29,   186.7926), (1464045328.29,   187.7334), (1464045329.31,   188.8143), (1464045330.32,   189.5488), (1464045331.34,   190.5459), (1464045332.36,   191.5642), (1464045333.38,   192.3424), (1464045334.39,   193.2665), (1464045335.41,   194.2089), (1464045336.41,   195.3092), (1464045337.43,   196.0099), (1464045338.43,   196.8646), (1464045339.45,   198.1758), (1464045340.45,   198.7704), (1464045341.47,   199.6762), (1464045342.48,   200.5995), (1464045343.49,   201.5410), (1464045344.5,   202.1790), (1464045345.51,   203.3165), (1464045346.52,   203.6465), (1464045347.53,   204.4815), (1464045348.54,   204.9896), (1464045349.55,   205.6755), (1464045350.56,   205.8485), (1464045351.58,   206.1965), (1464045352.59,   206.5469), (1464045353.61,   206.7231), (1464045354.63,   206.8999), (1464045355.65,   206.8999), (1464045356.66,   206.8999), (1464045357.67,   206.8999), 
(1464045358.69,   207.0774), (1464045359.7,   206.5469), (1464045360.7,   206.7231), (1464045361.72,   206.7231), (1464045362.73,   206.0222), (1464045363.74,   205.8485), (1464045364.75,   205.3313), (1464045365.77,   205.1602), (1464045366.78,   204.9896), (1464045367.78,   204.6503), (1464045368.8,   204.1458), (1464045369.81,   203.6465), (1464045370.82,   203.4812), (1464045371.84,   202.9887), (1464045372.84,   202.5013), (1464045373.85,   202.1790), (1464045374.86,   201.8589), (1464045375.87,   201.2251), (1464045376.88,   200.9113), (1464045377.89,   200.4444), (1464045378.9,   199.9820), (1464045379.91,   199.6762), (1464045380.92,   199.0704), (1464045381.94,   198.6210), (1464045382.95,   198.0284), (1464045383.95,   197.8813), (1464045384.97,   197.4429), (1464045385.98,   197.0085), (1464045386.99,   196.7211), (1464045388.0,   196.5780), (1464045389.03,   196.4353), (1464045390.04,   196.4353), (1464045391.05,   196.8646), (1464045392.06,   196.7211), (1464045393.09,   197.1529), (1464045394.1,   197.1529), (1464045395.11,   197.7347), (1464045396.13,   198.0284), (1464045397.13,   198.6210), (1464045398.15,   199.0704), (1464045399.15,   199.3724), (1464045400.17,   199.9820), (1464045401.18,   200.5995), (1464045402.19,   201.3828), (1464045403.2,   202.0187), (1464045404.21,   202.3399), (1464045405.23,   203.4812), (1464045406.24,   203.8123), (1464045407.26,   204.1458), (1464045408.27,   204.8196), (1464045409.28,   205.1602), (1464045410.3,   205.1602), (1464045411.31,   205.5031), (1464045412.32,   205.6755), (1464045413.33,   205.5031), (1464045414.34,   205.5031), (1464045415.35,   205.3313), (1464045416.35,   205.1602), (1464045417.36,   205.5031), (1464045418.37,   205.1602), (1464045419.38,   204.8196), (1464045420.39,   204.6503), (1464045421.4,   204.4815), (1464045422.4,   204.1458), (1464045423.42,   204.1458), (1464045424.42,   203.6465), 
(1464045425.43,   203.3165), (1464045426.44,   202.9887), (1464045427.45,   202.6632), (1464045428.46,   202.3399), (1464045429.47,   202.0187), (1464045430.48,   201.0679), (1464045431.49,   200.7552), (1464045432.51,   200.7552), (1464045433.52,   200.2898), (1464045434.53,   199.8289), (1464045435.53,   199.5240), (1464045436.54,   198.9202), (1464045437.55,   198.4722), (1464045438.57,   198.0284), (1464045439.58,   197.5886), (1464045440.59,   197.2977), (1464045441.59,   196.8646), (1464045442.61,   196.5780), (1464045443.63,   196.5780), (1464045444.64,   196.5780), (1464045445.65,   196.2931), (1464045446.65,   196.2931), (1464045447.66,   196.2931), (1464045448.67,   196.1513), (1464045449.69,   196.4353), (1464045450.7,   196.5780), (1464045451.71,   196.7211), (1464045452.72,   196.8646), (1464045453.73,   197.2977), (1464045454.74,   197.5886), (1464045455.75,   197.7347), (1464045456.76,   198.0284), (1464045457.77,   198.4722), (1464045458.78,   198.9202), (1464045459.79,   199.2211), (1464045460.79,   199.8289), (1464045461.81,   200.2898), (1464045462.81,   200.5995), (1464045463.82,   201.0679), (1464045464.83,   201.6997), (1464045465.84,   202.0187), (1464045466.85,   202.5013), (1464045467.87,   202.5013), (1464045468.88,   203.1523), (1464045469.9,   203.4812), (1464045470.9,   203.3165), (1464045471.91,   203.6465), (1464045472.92,   203.6465), (1464045473.93,   203.6465), (1464045474.94,   203.6465), (1464045475.95,   203.8123), (1464045476.96,   203.4812), (1464045477.97,   203.1523), (1464045478.98,   203.1523), (1464045479.99,   202.6632), (1464045481.0,   202.5013), (1464045482.01,   202.5013), (1464045483.01,   202.0187), (1464045484.02,   201.8589), (1464045485.03,   201.3828), (1464045486.04,   201.2251), (1464045487.05,   200.7552), (1464045488.06,   200.4444), (1464045489.07,   200.1356), (1464045490.08,   199.8289), (1464045491.09,   199.3724), 
(1464045492.1,   198.9202), (1464045493.11,   198.7704), (1464045494.13,   198.1758), (1464045495.14,   197.8813), (1464045496.16,   197.5886), (1464045497.17,   197.1529), (1464045498.18,   196.8646), (1464045499.19,   196.7211), (1464045500.2,   196.7211), (1464045501.21,   196.5780), (1464045502.22,   196.7211), (1464045503.23,   196.5780), (1464045504.23,   196.7211), (1464045505.24,   196.8646), (1464045506.25,   197.2977), (1464045507.27,   197.2977), (1464045508.29,   197.5886), (1464045509.3,   197.7347), (1464045510.31,   198.1758), (1464045511.32,   198.3238), (1464045512.34,   198.6210), (1464045513.34,   198.9202), (1464045514.35,   199.5240), (1464045515.37,   199.5240), (1464045516.38,   200.1356), (1464045517.38,   200.4444), (1464045518.39,   201.0679), (1464045519.4,   201.3828), (1464045520.41,   201.8589), (1464045521.42,   202.3399), (1464045522.43,   202.6632), (1464045523.45,   202.9887), (1464045524.45,   202.9887), (1464045525.46,   203.4812), (1464045526.48,   203.3165), (1464045527.49,   203.3165), (1464045528.5,   203.4812), (1464045529.51,   203.4812), (1464045530.52,   203.4812), (1464045531.53,   203.3165), (1464045532.54,   203.3165), (1464045533.54,   202.8257), (1464045534.57,   202.5013), (1464045535.58,   202.5013), (1464045536.59,   202.0187), (1464045537.59,   201.8589), (1464045538.6,   202.0187), (1464045539.62,   201.2251), (1464045540.62,   201.2251), (1464045541.63,   200.9113), (1464045542.64,   200.5995), (1464045543.65,   200.2898), (1464045544.66,   199.6762), (1464045545.68,   199.2211)]


    class MyClass:
        def __init__(self):
            self.sleep = 0.1

    tune = Autotune_1(MyClass())

    data = np.array(zip(*data)[1])[100:]

    print(data)

    peaks = Util.detect_peaks(data, show=True)
    data = Util.smooth(data, 10)
    data = data[:-10]
    peaks = Util.detect_peaks(data, show=True)
    valleys = Util.detect_peaks(data, valley=True, show=True)
    tune.calculate_PID(data, times, peaks, valleys)
    print(tune.Kp)
    print(tune.Ki)
    print(tune.Kd)






