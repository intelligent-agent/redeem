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


class Autotune:
  def __init__(self,
               heater,
               temp=200.0,
               cycles=4,
               g=None,
               printer=None,
               pre_calibrate=False,
               tuning_algo="TL"):
    self.heater = heater
    self.steady_temperature = temp    # Steady state starting temperture
    self.cycles = cycles
    self.g = g
    self.printer = printer
    self.output_step = 10.0    # Degrees to step
    self.E = 1.0    # Hysteresis
    self.tuning_algorithm = tuning_algo    # Ziegler-Nichols
    self.starting_temp = 30.0
    self.pre_calibrate_temp = 100.0
    self.pre_calibrate_enabled = pre_calibrate
    self.plot_temps = []
    self.ambient_temp = 20.0

  def cancel(self):
    self.running = False

  def send_temperatures(self):
    while self.running:
      m105 = Gcode({"message": "M105", "prot": self.g.prot})
      self.printer.processor.resolve(m105)
      self.printer.processor.execute(m105)
      answer = m105.get_answer()
      m105.set_answer(answer[2:])    # strip away the "ok"
      self.printer.reply(m105)
      self.plot_temps.append("({}, {:10.4f})".format(time.time(),
                                                     self.heater.get_temperature_raw()))
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

    # Pre calibrate
    if self.pre_calibrate_enabled:
      self._pre_calibrate()

    # Start stepping temperatures
    self._tune()
    #logging.debug("Tuning data: "+str(self.temps))

    # Set the new PID settings
    self.heater.Kp = self.Kp
    self.heater.Ti = self.Ti
    self.heater.Td = self.Td

    # Clean stuff up
    self.heater.onoff_control = self.has_onoff_control
    self.running = False
    self.t.join()

    return True

  def _tune(self):
    logging.debug("Starting Tuning")
    self.temps = np.array([])
    self.times = np.array([])
    for cycle in range(self.cycles):
      logging.debug("Doing cycle: " + str(cycle))

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
        # Calculate gain skew
        logging.debug("th: {}, tl: {}".format(self.t_low, self.t_high))
        self.bias += (self.d * (self.t_high - self.t_low)) / (self.t_low + self.t_high)
        self.bias = np.clip(self.bias, 0.1, 0.9)
        self.d = 1.0 - self.bias if self.bias > 0.5 else self.bias

        if cycle > 1:
          logging.debug("Smoothing")
          self.smooth_temps = Util.smooth(self.temps, 1000)
          self.smooth_temps = self.smooth_temps[:-1000]    # Remove window length
          self.peaks = Util.detect_peaks(self.smooth_temps)
          self.valleys = Util.detect_peaks(self.smooth_temps, valley=True)
          logging.debug("peaks: " + str(self.peaks))
          logging.debug("valls: " + str(self.valleys))
          logging.debug("temps len: " + str(len(self.temps)) + " " + str(len(self.smooth_temps)))

          self.max_temp = self.temps[self.peaks[-1]]
          self.min_temp = self.temps[self.valleys[-1]]
          logging.debug("Max: " + str(self.max_temp))
          logging.debug("Min: " + str(self.min_temp))

          a = self.max_temp - self.min_temp
          self.Ku = (4.0 * self.d) / (np.pi * np.sqrt(a**2 + self.E**2))
          self.Pu = self.t_low + self.t_high

          # Tyreus-Luyben:
          if self.tuning_algorithm == "TL":
            self.Kp = 0.45 * self.Ku
            self.Ti = 2.2 * self.Pu
            self.Td = self.Pu / 6.3

          # Classic Zieger-Nichols
          elif self.tuning_algorithm == "ZN":
            self.Kp = 0.6 * self.Ku
            self.Ti = self.Pu / 2.0
            self.Td = self.Pu / 8.0

          print("Temperature diff: " + str(a) + " deg. C")
          print("Oscillation period: " + str(self.Pu) + " seconds")
          print("Ultimate gain: " + str(self.Ku))
          print("Kp: " + str(self.Kp))
          print("Ti: " + str(self.Ti))
          print("Td: " + str(self.Td))

      self.heater.max_power = self.bias + self.d
      logging.debug("Power set to " + str(self.heater.max_power))

    logging.debug("Cycles completed")
    self.heater.set_target_temperature(0)
    self.heater.max_power = 1.0

  def _pre_calibrate(self):
    logging.debug("Starting pre-calibrate")
    # Wait for temperature to reach < 30 deg.
    self.heater.set_target_temperature(0)
    while self.heater.get_temperature() > self.starting_temp:
      time.sleep(1)

    # Get the noise band from the thermistor
    self.noise_band = self.heater.get_noise_magnitude()
    # Rev B has a very low noise floor, so if 0 is returned,
    # set it to 0.5
    self.noise_band = self.noise_band
    logging.debug("Found noise magnitude: " + str(self.noise_band))

    current_temp = self.heater.get_temperature()
    # Set the heater at 25% max power
    self.heater.max_power = 0.25

    heatup_temps = []

    # Start heating at 25%
    dead_time = 0
    stop_temp = current_temp + 2.0 * self.noise_band
    self.heater.set_target_temperature(self.pre_calibrate_temp)
    while self.heater.get_temperature_raw() < stop_temp:
      time.sleep(0.1)
      dead_time += 0.1
      #heatup_temps.append( "({}, {:10.4f})".format(time.time(), self.heater.get_temperature_raw()) )
    logging.debug("Found dead time: " + str(dead_time))

    # Wait for heatup curve to establish
    stop_time = 2.0 * dead_time
    while stop_time > 0:
      time.sleep(0.1)
      #heatup_temps.append("({}, {:10.4f})".format(time.time(), self.heater.get_temperature_raw() ))
      stop_time -= 0.1

    # (5) Record slope of heat up curve
    delta_temps = []
    delta_times = []
    delta_time = np.minimum(np.maximum(dead_time * 4.0, 10.0), 30.0)
    self.delta_time = delta_time
    logging.debug("Starting delta measurements, time: " + str(delta_time))
    while delta_time > 0:
      delta_temps.append(self.heater.get_temperature_raw())
      delta_times.append(time.time())
      time.sleep(0.1)
      delta_time -= 0.1
      #heatup_temps.append("({}, {:10.4f})".format(time.time(), self.heater.get_temperature_raw() ))

    logging.debug("Stopping delta measurements")

    #logging.debug("Heatup temps: "+str(heatup_temps))

    # (6) Calculate heat-up rate
    heat_rate = (delta_temps[-1] - delta_temps[0]) / (delta_times[-1] - delta_times[0])
    logging.debug("heat up rate at 25%: " + str(heat_rate) + " deg/s")

    # (7) Calculate max heat rate
    self.max_heat_rate = heat_rate * 4.0    # * 1.16
    logging.debug("Max heat rate: " + str(self.max_heat_rate) + " deg/s")

    # (8) Estimate cutoff point
    self.cutoff_band = self.max_heat_rate * dead_time
    logging.debug("Cutoff band: " + str(self.cutoff_band) + " deg")

    # (9) Raise temp until cutoff.
    cutoff_temp = self.pre_calibrate_temp - self.cutoff_band
    self.heater.max_power = 1.0
    cutoff_temps = []
    cutoff_times = []
    logging.debug("Cutoff temp: " + str(cutoff_temp) + " deg")
    while self.heater.get_temperature_raw() < cutoff_temp:
      cutoff_temps.append(self.heater.get_temperature_raw())
      cutoff_times.append(time.time())
      time.sleep(0.1)

    # (10) Calculate slope in degrees/second, store as setpoint_heating_rate
    self.setpoint_heating_rate = (cutoff_temps[-1] - cutoff_temps[-20]) / (
        cutoff_times[-1] - cutoff_times[-20])
    logging.debug("Found setpoint heating rate: " + str(self.setpoint_heating_rate))

    if self.setpoint_heating_rate > self.max_heat_rate:
      self.max_heat_rate = self.setpoint_heating_rate
      logging.debug("Updated max heat rate to: " + str(self.setpoint_heating_rate))

    # (11) Set power to zero
    self.heater.set_target_temperature(0)
    logging.debug("Disabling heater and looking for peak")

    # (12) Find temp peak
    highest_temp = self.heater.get_temperature_raw()
    new_temp = highest_temp
    while new_temp >= highest_temp:
      time.sleep(0.1)
      highest_temp = new_temp
      new_temp = self.heater.get_temperature_raw()
    logging.debug("Found max peak: " + str(highest_temp) + " deg")

    # (13) Adding dead time
    dead_time = highest_temp - 20
    while self.heater.get_temperature_raw() > dead_time:
      time.sleep(0.1)

    # (14) Record cooling rates
    logging.debug("Started recording cooling rates")
    cooling_temps = []
    cooling_times = []
    cooldown_temps = []
    # Get 120 seconds of cooling data
    for temp in range(1200):
      cooling_temps.append(self.heater.get_temperature_raw())
      cooling_times.append(time.time())
      time.sleep(0.1)
      #cooldown_temps.append("({}, {:10.4f})".format(time.time(), self.heater.get_temperature_raw() ))

    #temps = ",".join(cooldown_temps)
    #logging.debug("Cooling temps: "+str(temps))

    diffs = np.array(
        [(cooling_temps[200 + (i * 200)] - cooling_temps[0 + (i * 200)]) for i in range(5)])
    times = np.array(
        [(cooling_times[200 + (i * 200)] - cooling_times[0 + (i * 200)]) for i in range(5)])
    slopes = abs(diffs / times)
    temp_deltas = [cooling_temps[100 + (i * 200)] - self.ambient_temp for i in range(5)]

    # Wait until we are below cutoff-temp, so we can get some traction
    while self.heater.get_temperature_raw() > cutoff_temp - 20.0:
      time.sleep(1)

    # (15) Record setpoint cooling rate
    self.cooling_rate = slopes[0]

    logging.debug("Cooling rate: " + str(self.cooling_rate) + " deg/s")
    logging.debug("Diffs: " + str(diffs) + " deg")
    logging.debug("Times: " + str(times) + " s")
    logging.debug("Cooling rates: " + str(slopes) + " deg/s")
    logging.debug("Deltas: " + str(temp_deltas) + " deg")

    # (16) Calculate heat_loss_constant
    self.heat_loss_constant = [slopes[n] / temp_deltas[n] for n in range(len(slopes))]
    logging.debug("Heat loss constant: " + str(self.heat_loss_constant))

    # (17) Calculate heat_loss_K
    self.heat_loss_k = np.average(self.heat_loss_constant)
    logging.debug("Heat loss K: " + str(self.heat_loss_k))

    # (19) Calculate gain skew
    self.gain_skew = np.sqrt(self.setpoint_heating_rate / self.cooling_rate)

    logging.debug("Gain skew: " + str(self.gain_skew))

    # (20) Calculate rate of heat loss in degrees/second at desired setpoint using heat loss model,
    setpoint_loss = self.heat_loss_k * (self.steady_temperature - self.ambient_temp)
    logging.debug("Setpoint loss: " + str(setpoint_loss))

    # (21) Calculate setpoint heater power requirement,
    self.setpoint_power = setpoint_loss / self.max_heat_rate
    logging.debug("Setpoint_power: " + str(self.setpoint_power))

    # (22) Calculate high-cycle power
    self.high_cycle_power = self.setpoint_power * (1.0 + 1.0 / (self.gain_skew**2))
    logging.debug("High-cycle_power: " + str(self.high_cycle_power))

    # (23) Check if high-cycle power exceeds max_PWM
    if self.high_cycle_power > 1.0:
      # notify user the heater is too weak to cycle effectively at the chosen setpoint,
      # and change setpoint_power=max_PWM/2, ignore gain_skew, and use high-cycle power = max_PWM.
      # TODO: fix this
      logging.warning("High cycle power exceedes max. Setting to 1.0")
      self.high_cycle_power = 1.0

    # Apply max heater power until reaching temp=setpoint - cutoff_band

    cutoff_temp = self.steady_temperature - self.cutoff_band
    self.heater.max_power = 1.0
    self.heater.set_target_temperature(self.steady_temperature)
    logging.debug("Cutoff temp: " + str(cutoff_temp) + " deg")
    while self.heater.get_temperature_raw() < cutoff_temp:
      time.sleep(0.1)
    logging.debug("Cutoff temp reached")

    self.heater.set_target_temperature(0)
    logging.debug("Disabling heater and looking for peak")

    highest_temp = self.heater.get_temperature_raw()
    new_temp = highest_temp
    while new_temp >= highest_temp:
      time.sleep(0.1)
      highest_temp = new_temp
      new_temp = self.heater.get_temperature_raw()
    logging.debug("Found max peak: " + str(highest_temp) + " deg")

    # (6) Apply setpoint_power heater power and hold until stable
    self.heater.max_power = self.setpoint_power
    # Set temp to something above the desired. setpoint power should enforce this.
    #self.heater.set_target_temperature(230)
    #while self.heater.get_noise_magnitude(300) > 1.0:
    #    time.sleep(1)

    #logging.debug("Stable temp reached")

    self.heater.max_power = self.high_cycle_power

    logging.debug("Pre calibrate done")


# yapf: disable
if __name__ == "__main__":
  import matplotlib.pyplot as plt

  data = [
      (226.10,    93.8263), (227.12,    93.6712), (228.12,    93.4540),
      (229.14,    93.3919), (230.15,    93.2677), (231.16,    93.3298),
      (232.17,    93.4540), (233.18,    93.6712), (234.20,    93.9194),
      (235.21,    94.2916), (236.22,    94.7257), (237.22,    95.3146),
      (238.24,    95.8725), (239.25,    96.5235), (240.26,    97.2366),
      (241.27,    98.0122), (242.28,    98.9129), (243.28,    99.7837),
      (244.30,   100.6250), (245.31,   101.6243), (246.32,   102.5326),
      (247.32,   103.5381), (248.33,   104.4844), (249.35,   105.5616),
      (250.36,   106.5487), (251.37,   107.6053), (252.38,   108.7007),
      (253.40,   109.8036), (254.41,   110.9149), (255.42,   111.9690),
      (256.43,   113.0985), (257.44,   114.2048), (258.45,   115.3217),
      (259.46,   116.4500), (260.47,   117.5210), (261.49,   118.6738),
      (262.50,   119.9116), (263.51,   120.9858), (264.53,   122.0730),
      (265.54,   123.3589), (266.55,   124.4020), (267.57,   125.5346),
      (268.58,   126.7223), (269.59,   127.9286), (270.61,   128.9556),
      (271.61,   130.1588), (272.63,   131.3826), (273.63,   132.5864),
      (274.65,   133.6415), (275.66,   134.7567), (276.68,   135.8472),
      (277.69,   137.0460), (278.71,   138.1309), (279.72,   139.2814),
      (280.73,   140.4539), (281.74,   141.5048), (282.75,   142.5744),
      (283.76,   143.7138), (284.77,   144.8759), (285.79,   145.9059),
      (286.80,   147.0077), (287.81,   148.1316), (288.82,   149.1682),
      (289.83,   150.1685), (290.84,   151.4165), (291.85,   152.4009),
      (292.87,   153.4631), (293.88,   154.5468), (294.89,   155.5291),
      (295.90,   156.6565), (296.91,   157.6148), (297.92,   158.5255),
      (298.93,   159.7203), (299.94,   160.7377), (300.95,   161.7757),
      (301.96,   162.8352), (302.98,   163.7717), (303.98,   164.8744),
      (304.99,   165.7742), (306.01,   166.6905), (307.02,   167.7813),
      (308.04,   168.8160), (309.05,   169.7906), (310.06,   170.7849),
      (311.08,   171.6291), (312.09,   172.6616), (313.10,   173.6276),
      (314.11,   174.6130), (315.13,   175.5265), (316.15,   176.4574),
      (317.17,   177.6949), (318.19,   178.2769), (319.20,   179.2627),
      (320.21,   180.4728), (321.21,   181.1929), (322.22,   182.2407),
      (323.24,   183.0957), (324.25,   184.0761), (325.26,   185.0768),
      (326.28,   186.0989), (327.29,   186.7926), (328.29,   187.7334),
      (329.31,   188.8143), (330.32,   189.5488), (331.34,   190.5459),
      (332.36,   191.5642), (333.38,   192.3424), (334.39,   193.2665),
      (335.41,   194.2089), (336.41,   195.3092), (337.43,   196.0099),
      (338.43,   196.8646), (339.45,   198.1758), (340.45,   198.7704),
      (341.47,   199.6762), (342.48,   200.5995), (343.49,   201.5410),
      (344.50,   202.1790), (345.51,   203.3165), (346.52,   203.6465),
      (347.53,   204.4815), (348.54,   204.9896), (349.55,   205.6755),
      (350.56,   205.8485), (351.58,   206.1965), (352.59,   206.5469),
      (353.61,   206.7231), (354.63,   206.8999), (355.65,   206.8999),
      (356.66,   206.8999), (357.67,   206.8999), (358.69,   207.0774),
      (359.70,   206.5469), (360.70,   206.7231), (361.72,   206.7231),
      (362.73,   206.0222), (363.74,   205.8485), (364.75,   205.3313),
      (365.77,   205.1602), (366.78,   204.9896), (367.78,   204.6503),
      (368.80,   204.1458), (369.81,   203.6465), (370.82,   203.4812),
      (371.84,   202.9887), (372.84,   202.5013), (373.85,   202.1790),
      (374.86,   201.8589), (375.87,   201.2251), (376.88,   200.9113),
      (377.89,   200.4444), (378.90,   199.9820), (379.91,   199.6762),
      (380.92,   199.0704), (381.94,   198.6210), (382.95,   198.0284),
      (383.95,   197.8813), (384.97,   197.4429), (385.98,   197.0085),
      (386.99,   196.7211), (388.00,   196.5780), (389.03,   196.4353),
      (390.04,   196.4353), (391.05,   196.8646), (392.06,   196.7211),
      (393.09,   197.1529), (394.10,   197.1529), (395.11,   197.7347),
      (396.13,   198.0284), (397.13,   198.6210), (398.15,   199.0704),
      (399.15,   199.3724), (400.17,   199.9820), (401.18,   200.5995),
      (402.19,   201.3828), (403.20,   202.0187), (404.21,   202.3399),
      (405.23,   203.4812), (406.24,   203.8123), (407.26,   204.1458),
      (408.27,   204.8196), (409.28,   205.1602), (410.30,   205.1602),
      (411.31,   205.5031), (412.32,   205.6755), (413.33,   205.5031),
      (414.34,   205.5031), (415.35,   205.3313), (416.35,   205.1602),
      (417.36,   205.5031), (418.37,   205.1602), (419.38,   204.8196),
      (420.39,   204.6503), (421.40,   204.4815), (422.40,   204.1458),
      (423.42,   204.1458), (424.42,   203.6465), (425.43,   203.3165),
      (426.44,   202.9887), (427.45,   202.6632), (428.46,   202.3399),
      (429.47,   202.0187), (430.48,   201.0679), (431.49,   200.7552),
      (432.51,   200.7552), (433.52,   200.2898), (434.53,   199.8289),
      (435.53,   199.5240), (436.54,   198.9202), (437.55,   198.4722),
      (438.57,   198.0284), (439.58,   197.5886), (440.59,   197.2977),
      (441.59,   196.8646), (442.61,   196.5780), (443.63,   196.5780),
      (444.64,   196.5780), (445.65,   196.2931), (446.65,   196.2931),
      (447.66,   196.2931), (448.67,   196.1513), (449.69,   196.4353),
      (450.70,   196.5780), (451.71,   196.7211), (452.72,   196.8646),
      (453.73,   197.2977), (454.74,   197.5886), (455.75,   197.7347),
      (456.76,   198.0284), (457.77,   198.4722), (458.78,   198.9202),
      (459.79,   199.2211), (460.79,   199.8289), (461.81,   200.2898),
      (462.81,   200.5995), (463.82,   201.0679), (464.83,   201.6997),
      (465.84,   202.0187), (466.85,   202.5013), (467.87,   202.5013),
      (468.88,   203.1523), (469.90,   203.4812), (470.90,   203.3165),
      (471.91,   203.6465), (472.92,   203.6465), (473.93,   203.6465),
      (474.94,   203.6465), (475.95,   203.8123), (476.96,   203.4812),
      (477.97,   203.1523), (478.98,   203.1523), (479.99,   202.6632),
      (481.00,   202.5013), (482.01,   202.5013), (483.01,   202.0187),
      (484.02,   201.8589), (485.03,   201.3828), (486.04,   201.2251),
      (487.05,   200.7552), (488.06,   200.4444), (489.07,   200.1356),
      (490.08,   199.8289), (491.09,   199.3724), (492.10,   198.9202),
      (493.11,   198.7704), (494.13,   198.1758), (495.14,   197.8813),
      (496.16,   197.5886), (497.17,   197.1529), (498.18,   196.8646),
      (499.19,   196.7211), (500.20,   196.7211), (501.21,   196.5780),
      (502.22,   196.7211), (503.23,   196.5780), (504.23,   196.7211),
      (505.24,   196.8646), (506.25,   197.2977), (507.27,   197.2977),
      (508.29,   197.5886), (509.30,   197.7347), (510.31,   198.1758),
      (511.32,   198.3238), (512.34,   198.6210), (513.34,   198.9202),
      (514.35,   199.5240), (515.37,   199.5240), (516.38,   200.1356),
      (517.38,   200.4444), (518.39,   201.0679), (519.40,   201.3828),
      (520.41,   201.8589), (521.42,   202.3399), (522.43,   202.6632),
      (523.45,   202.9887), (524.45,   202.9887), (525.46,   203.4812),
      (526.48,   203.3165), (527.49,   203.3165), (528.50,   203.4812),
      (529.51,   203.4812), (530.52,   203.4812), (531.53,   203.3165),
      (532.54,   203.3165), (533.54,   202.8257), (534.57,   202.5013),
      (535.58,   202.5013), (536.59,   202.0187), (537.59,   201.8589),
      (538.60,   202.0187), (539.62,   201.2251), (540.62,   201.2251),
      (541.63,   200.9113), (542.64,   200.5995), (543.65,   200.2898),
      (544.66,   199.6762), (545.68,   199.2211)
      ]
  # yapf: enable


  class MyClass:
    def __init__(self):
      self.sleep = 0.1

  tune = Autotune(MyClass())

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
