/*
 This file is part of Redeem - 3D Printer control software
 
 Author: Mathieu Monney
 Website: http://www.xwaves.net
 License: GNU GPLv3 http://www.gnu.org/copyleft/gpl.html
 
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
 
 */

#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION

#ifndef PathPlanner_config_h
#define PathPlanner_config_h

/* Number of axis needed to move the printer head. Only 3 supported */
#define NUM_MOVING_AXES 3

/* Total number of axis that the system supports, including the currently selected extruder. */
#define NUM_AXES 8

/* Number of extruder */
#define NUM_EXTRUDER 5

/* The speed of the timer created by the PRU in Hz */
#define F_CPU 200000000
#define F_CPU_FLOAT 200000000.0
#define CPU_CYCLE_LENGTH (1.0/200000000.0) // AKA 5e-9

/* Data type for floating point */
#define FLOAT_T double

/* Negligible numeric error - also 1/50th of a CPU cycle */
#define NEGLIGIBLE_ERROR 1e-10

#define AXIS_CONFIG_XY      0
#define AXIS_CONFIG_H_BELT  1
#define AXIS_CONFIG_CORE_XY 2
#define AXIS_CONFIG_DELTA   3

#endif
