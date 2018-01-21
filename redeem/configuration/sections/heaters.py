from redeem.configuration.sections import BaseConfig


class HeatersConfig(BaseConfig):
    # For list of available temp charts, look in temp_chart.py

    sensor_e = 'B57560G104F'
    pid_kp_e = 0.1
    pid_ti_e = 100.0
    pid_td_e = 0.3
    ok_range_e = 4.0
    max_rise_temp_e = 10.0
    max_fall_temp_e = 10.0
    min_temp_e = 20.0
    max_temp_e = 250.0
    path_adc_e = '/sys/bus/iio/devices/iio:device0/in_voltage4_raw'
    mosfet_e = 5
    onoff_e = False
    prefix_e = 'T0'
    max_power_e = 1.0

    sensor_h = 'B57560G104F'
    pid_kp_h = 0.1
    pid_ti_h = 0.01
    pid_td_h = 0.3
    ok_range_h = 4.0
    max_rise_temp_h = 10.0
    max_fall_temp_h = 10.0
    min_temp_h = 20.0
    max_temp_h = 250.0
    path_adc_h = '/sys/bus/iio/devices/iio:device0/in_voltage5_raw'
    mosfet_h = 3
    onoff_h = False
    prefix_h = 'T1'
    max_power_h = 1.0

    sensor_a = 'B57560G104F'
    pid_kp_a = 0.1
    pid_ti_a = 0.01
    pid_td_a = 0.3
    ok_range_a = 4.0
    max_rise_temp_a = 10.0
    max_fall_temp_a = 10.0
    min_temp_a = 20.0
    max_temp_a = 250.0
    path_adc_a = '/sys/bus/iio/devices/iio:device0/in_voltage0_raw'
    mosfet_a = 11
    onoff_a = False
    prefix_a = 'T2'
    max_power_a = 1.0

    sensor_b = 'B57560G104F'
    pid_kp_b = 0.1
    pid_ti_b = 0.01
    pid_td_b = 0.3
    ok_range_b = 4.0
    max_rise_temp_b = 10.0
    max_fall_temp_b = 10.0
    min_temp_b = 20.0
    max_temp_b = 250.0
    path_adc_b = '/sys/bus/iio/devices/iio:device0/in_voltage3_raw'
    mosfet_b = 12
    onoff_b = False
    prefix_b = 'T3'
    max_power_b = 1.0

    sensor_c = 'B57560G104F'
    pid_kp_c = 0.1
    pid_ti_c = 0.01
    pid_td_c = 0.3
    ok_range_c = 4.0
    max_rise_temp_c = 10.0
    max_fall_temp_c = 10.0
    min_temp_c = 20.0
    max_temp_c = 250.0
    path_adc_c = '/sys/bus/iio/devices/iio:device0/in_voltage2_raw'
    mosfet_c = 13
    onoff_c = False
    prefix_c = 'T4'
    max_power_c = 1.0

    sensor_hbp = 'B57560G104F'
    pid_kp_hbp = 0.1
    pid_ti_hbp = 0.01
    pid_td_hbp = 0.3
    ok_range_hbp = 4.0
    max_rise_temp_hbp = 10.0
    max_fall_temp_hbp = 10.0
    min_temp_hbp = 20.0
    max_temp_hbp = 250.0
    path_adc_hbp = '/sys/bus/iio/devices/iio:device0/in_voltage6_raw'
    mosfet_hbp = 4
    onoff_hbp = False
    prefix_hbp = 'B'
    max_power_hbp = 1.0
