from redeem.configuration.sections import BaseConfig


class GeometryConfig(BaseConfig):
    axis_config = 0  # 0 - Cartesian, 1 - H-belt, 2 - Core XY,  3 - Delta

    # The total length each axis can travel, this affects the homing endstop searching length.
    travel_x, travel_y, travel_z = 0.2, 0.2, 0.2
    travel_e, travel_h = 0.2, 0.2
    travel_a, travel_b, travel_c = 0.0, 0.0, 0.0

    # Define the origin of the build plate in relation to the endstops
    offset_x, offset_y, offset_z = 0.0, 0.0, 0.0
    offset_e, offset_h = 0.0, 0.0
    offset_a, offset_b, offset_c = 0.0, 0.0, 0.0

    bed_compensation_matrix = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
