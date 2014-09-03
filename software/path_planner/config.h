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

#ifndef PathPlanner_config_h
#define PathPlanner_config_h

/* Number of axis needed to move the printer head. Only 3 supported */
#define NUM_MOVING_AXIS 3

/* Total number of axis that the system supports, including the currently selected extruder. Currently only 4 is supported */
#define NUM_AXIS 4

/* Number of move to cache to execute the path planner on. */
#define MOVE_CACHE_SIZE 128

/* Number of extruder */
#define NUM_EXTRUDER 2

/* The speed of the timer created by the PRU in Hz */
#define F_CPU 200000000

/* Minimum of move buffered in the PRU (in term of move time in milliseconds) before we stop sending moves to the PRU. */
/* Should be as low as possible so that we can keep some moves in the PathPlanner buffer for proper speed computations */
#define MIN_BUFFERED_MOVE_TIME 100

/* Time to wait before processing a print command if the buffer is not full enough, expressed in milliseconds. 
 * Increasing this time will reduce the slow downs due to the path planner not having enough path in the buffer 
 * but it will increase the startup time of the print.
 */
#define PRINT_MOVE_BUFFER_WAIT 500

/* Data type for floating point */
#define FLOAT_T double

#endif
