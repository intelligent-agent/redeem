from redeem.configuration.sections import BaseConfig


class ColdendsConfig(BaseConfig):
    # To use the DS18B20 temp sensors, connect them like this, enable by setting to True
    connect_ds18b20_0_fan_0 = False
    connect_ds18b20_1_fan_0 = False
    connect_ds18b20_0_fan_1 = False

    # This list is for connecting thermistors to fans, so they are controlled automatically when reaching 60 degrees.
    connect_therm_e_fan_0 = False
    connect_therm_e_fan_1 = False
    connect_therm_e_fan_2 = False
    connect_therm_e_fan_3 = False
    connect_therm_h_fan_0 = False
    connect_therm_h_fan_1 = False
    connect_therm_h_fan_2 = False
    connect_therm_h_fan_3 = False
    connect_therm_a_fan_0 = False
    connect_therm_a_fan_1 = False
    connect_therm_a_fan_2 = False
    connect_therm_a_fan_3 = False
    connect_therm_b_fan_0 = False
    connect_therm_b_fan_1 = False
    connect_therm_b_fan_2 = False
    connect_therm_b_fan_3 = False
    connect_therm_c_fan_0 = False
    connect_therm_c_fan_1 = False
    connect_therm_c_fan_2 = False
    connect_therm_c_fan_3 = False
    connect_therm_hbp_fan_0 = False
    connect_therm_hbp_fan_1 = False
    connect_therm_hbp_fan_2 = False
    connect_therm_hbp_fan_3 = False

    add_fan_0_to_m106 = False
    add_fan_1_to_m106 = False
    add_fan_2_to_m106 = False
    add_fan_3_to_m106 = False

    cooler_0_target_temp = 60  # If you want coolers to have a different 'keep' temp, list it here.

    # If you want the fan-thermitor connetions to have a
    # different temperature:
    # therm-e-fan-0-target_temp = 70