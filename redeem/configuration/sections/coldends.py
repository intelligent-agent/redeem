from redeem.configuration.sections import BaseConfig


class ColdendsConfig(BaseConfig):
    # To use the DS18B20 temp sensors, connect them like this, enable by setting to True
    connect_ds18b20_0_fan_0 = False
    connect_ds18b20_1_fan_0 = False
    connect_ds18b20_0_fan_1 = False

    # This list is for connecting thermistors to fans, so they are controlled automatically when reaching 60 degrees.
    connect_therm_E_fan_0 = False
    connect_therm_E_fan_1 = False
    connect_therm_E_fan_2 = False
    connect_therm_E_fan_3 = False
    connect_therm_H_fan_0 = False
    connect_therm_H_fan_1 = False
    connect_therm_H_fan_2 = False
    connect_therm_H_fan_3 = False
    connect_therm_A_fan_0 = False
    connect_therm_A_fan_1 = False
    connect_therm_A_fan_2 = False
    connect_therm_A_fan_3 = False
    connect_therm_B_fan_0 = False
    connect_therm_B_fan_1 = False
    connect_therm_B_fan_2 = False
    connect_therm_B_fan_3 = False
    connect_therm_C_fan_0 = False
    connect_therm_C_fan_1 = False
    connect_therm_C_fan_2 = False
    connect_therm_C_fan_3 = False
    connect_therm_HBP_fan_0 = False
    connect_therm_HBP_fan_1 = False
    connect_therm_HBP_fan_2 = False
    connect_therm_HBP_fan_3 = False

    add_fan_0_to_M106 = False
    add_fan_1_to_M106 = False
    add_fan_2_to_M106 = False
    add_fan_3_to_M106 = False

    cooler_0_target_temp = 60  # If you want coolers to have a different 'keep' temp, list it here.

    # If you want the fan-thermitor connetions to have a
    # different temperature:
    # therm-e-fan-0-target_temp = 70

    def get(self, key):
        key = key.replace('_', '-')

        if not getattr(self, key, None):
            return None
        return getattr(self, key)
