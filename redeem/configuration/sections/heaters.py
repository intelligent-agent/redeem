from redeem.configuration.sections import BaseConfig


class HeatersConfig(BaseConfig):
    # For list of available temp charts, look in temp_chart.py

    sensor_E = 'B57560G104F'
    pid_Kp_E = 0.1
    pid_Ti_E = 100.0
    pid_Td_E = 0.3
    ok_range_E = 4.0
    max_rise_temp_E = 10.0
    max_fall_temp_E = 10.0
    min_temp_E = 20.0
    max_temp_E = 250.0
    path_adc_E = '/sys/bus/iio/devices/iio:device0/in_voltage4_raw'
    mosfet_E = 5
    onoff_E = False
    prefix_E = 'T0'
    max_power_E = 1.0

    sensor_H = 'B57560G104F'
    pid_Kp_H = 0.1
    pid_Ti_H = 0.01
    pid_Td_H = 0.3
    ok_range_H = 4.0
    max_rise_temp_H = 10.0
    max_fall_temp_H = 10.0
    min_temp_H = 20.0
    max_temp_H = 250.0
    path_adc_H = '/sys/bus/iio/devices/iio:device0/in_voltage5_raw'
    mosfet_H = 3
    onoff_H = False
    prefix_H = 'T1'
    max_power_H = 1.0

    sensor_A = 'B57560G104F'
    pid_Kp_A = 0.1
    pid_Ti_A = 0.01
    pid_Td_A = 0.3
    ok_range_A = 4.0
    max_rise_temp_A = 10.0
    max_fall_temp_A = 10.0
    min_temp_A = 20.0
    max_temp_A = 250.0
    path_adc_A = '/sys/bus/iio/devices/iio:device0/in_voltage0_raw'
    mosfet_A = 11
    onoff_A = False
    prefix_A = 'T2'
    max_power_A = 1.0

    sensor_B = 'B57560G104F'
    pid_Kp_B = 0.1
    pid_Ti_B = 0.01
    pid_Td_B = 0.3
    ok_range_B = 4.0
    max_rise_temp_B = 10.0
    max_fall_temp_B = 10.0
    min_temp_B = 20.0
    max_temp_B = 250.0
    path_adc_B = '/sys/bus/iio/devices/iio:device0/in_voltage3_raw'
    mosfet_B = 12
    onoff_B = False
    prefix_B = 'T3'
    max_power_B = 1.0

    sensor_C = 'B57560G104F'
    pid_Kp_C = 0.1
    pid_Ti_C = 0.01
    pid_Td_C = 0.3
    ok_range_C = 4.0
    max_rise_temp_C = 10.0
    max_fall_temp_C = 10.0
    min_temp_C = 20.0
    max_temp_C = 250.0
    path_adc_C = '/sys/bus/iio/devices/iio:device0/in_voltage2_raw'
    mosfet_C = 13
    onoff_C = False
    prefix_C = 'T4'
    max_power_C = 1.0

    sensor_HBP = 'B57560G104F'
    pid_Kp_HBP = 0.1
    pid_Ti_HBP = 0.01
    pid_Td_HBP = 0.3
    ok_range_HBP = 4.0
    max_rise_temp_HBP = 10.0
    max_fall_temp_HBP = 10.0
    min_temp_HBP = 20.0
    max_temp_HBP = 250.0
    path_adc_HBP = '/sys/bus/iio/devices/iio:device0/in_voltage6_raw'
    mosfet_HBP = 4
    onoff_HBP = False
    prefix_HBP = 'B'
    max_power_HBP = 1.0
