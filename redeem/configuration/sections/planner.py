from redeem.configuration.sections import BaseConfig


class PlannerConfig(BaseConfig):

    move_cache_size = 1024                  # size of the path planning cache
    print_move_buffer_wait = 250            # time to wait for buffer to fill, (ms)

    # total buffered move time should not exceed this much (ms)
    max_buffered_move_time = 1000

    acceleration_x, acceleration_y, acceleration_z = 0.5, 0.5, 0.5
    acceleration_e, acceleration_h = 0.5, 0.5
    acceleration_a, acceleration_b, acceleration_c = 0.5, 0.5, 0.5

    max_jerk_x, max_jerk_y, max_jerk_z = 0.01, 0.01, 0.01
    max_jerk_e, max_jerk_h = 0.01, 0.01
    max_jerk_a, max_jerk_b, max_jerk_c = 0.01, 0.01, 0.01

    # Max speed for the steppers in m/s
    max_speed_x, max_speed_y, max_speed_z = 0.2, 0.2, 0.02
    max_speed_e, max_speed_h = 0.2, 0.2
    max_speed_a, max_speed_b, max_speed_c = 0.2, 0.2, 0.2

    arc_segment_length = 0.001              # for arc commands, seperate into segments of length in m

    # When true, movements on the E axis (eg, G1, G92) will apply
    # to the active tool (similar to other firmwares).  When false,
    # such movements will only apply to the E axis.
    e_axis_active = True
