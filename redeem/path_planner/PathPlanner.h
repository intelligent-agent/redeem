/*
 This file is part of Redeem - 3D Printer control software
 
 Author: Mathieu Monney
 Website: http://www.xwaves.net
 License: GNU GPLv3 http://www.gnu.org/copyleft/gpl.html
 
 
 This file is based on Repetier-Firmware licensed under GNU GPL v3 and
 available at https://github.com/repetier/Repetier-Firmware
 
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

#ifndef __PathPlanner__PathPlanner__
#define __PathPlanner__PathPlanner__

#include <iostream>
#include <atomic>
#include <thread>
#include <vector>
#include <mutex>
#include <string.h>
#include <strings.h>
#include <assert.h>
#include "PruTimer.h"
#include "Path.h"
#include "config.h"

class Extruder {
private:
	FLOAT_T maxStartFeedrate;
	FLOAT_T maxFeedrate;
	unsigned long maxPrintAccelerationStepsPerSquareSecond;
	unsigned long maxTravelAccelerationStepsPerSquareSecond;
	unsigned long maxAccelerationMMPerSquareSecond;
	unsigned long maxTravelAccelerationMMPerSquareSecond;
	FLOAT_T invAxisStepsPerMM;
	unsigned long axisStepsPerMM;
	bool directionInverted;
	
	void recomputeParameters();
	
	unsigned int stepperCommandPosition;

public:
	
	/**
	 * @brief Set the maximum feedrate of the extruder
	 * @details Set the maximum feedrate of the extruder in m/s
	 *
	 * @param rates The feedrate of the extruder
	 */
	void setMaxFeedrate(FLOAT_T rate);
	
	/**
	 * @brief Set the maximum speed at which the extruder can start
	 * @details Set the maximum speed at which the extruder can start
	 *
	 * @param maxstartfeedrate the maximum speed at which the extruder can start in m/s
	 */
	void setMaxStartFeedrate(FLOAT_T maxstartfeedrate);
	
	/**
	 * @brief Set the number of steps required to move each axis by 1 meter
	 * @details Set the number of steps required to move each axis by 1 meter
	 *
	 * @param stepPerM the number of steps required to move each axis by 1 meter, consisting of a NUM_AXIS length array.
	 */
	void setAxisStepsPerMeter(unsigned long stepPerM);
	
	/**
	 * @brief Set the max acceleration for printing moves
	 * @details Set the max acceleration for moves when the extruder is activated
	 *
	 * @param accel The acceleration in m/s^2
	 */
	void setPrintAcceleration(FLOAT_T accel);
	
	/**
	 * @brief Set the max acceleration for travel moves
	 * @details Set the max acceleration for moves when the extruder is not activated (i.e. not printing)
	 *
	 * @param accel The acceleration in m/s^2
	 */
	void setTravelAcceleration(FLOAT_T accel);
	
	/**
	 * @brief Return the bit that needs to be tiggled for setting direction and step pin of the stepper driver for this extruder
	 * @return the bit that needs to be tiggled for setting direction and step pin of the stepper driver for this extruder
	 *
	 */
	inline unsigned int getStepperCommandPosition() {
		return stepperCommandPosition;
	}
	
	inline void setStepperCommandPosition(unsigned int pose) {
		stepperCommandPosition = pose;
	}
	
	inline void setDirectionInverted(bool inverted) {
		directionInverted = inverted;
	}
	
	friend class PathPlanner;
};

class PathPlanner {
private:
	void calculateMove(Path* p,FLOAT_T axis_diff[NUM_AXIS]);
	FLOAT_T safeSpeed(Path *p);
	void updateTrapezoids();
	void computeMaxJunctionSpeed(Path *previous,Path *current);
	void backwardPlanner(unsigned int start,unsigned int last);
	void forwardPlanner(unsigned int first);
	
	FLOAT_T maxFeedrate[NUM_AXIS];
	unsigned long maxPrintAccelerationStepsPerSquareSecond[NUM_AXIS];
	unsigned long maxTravelAccelerationStepsPerSquareSecond[NUM_AXIS];
	unsigned long maxAccelerationMMPerSquareSecond[NUM_AXIS];
	unsigned long maxTravelAccelerationMMPerSquareSecond[NUM_AXIS];
	
	Extruder extruders[NUM_EXTRUDER];
	
	Extruder* currentExtruder;
	
	FLOAT_T maxJerk;
	FLOAT_T maxZJerk;
	
	FLOAT_T minimumSpeed;
	FLOAT_T minimumZSpeed;
			
	FLOAT_T invAxisStepsPerMM[NUM_AXIS];
	unsigned long axisStepsPerMM[NUM_AXIS];

    int driveSystem;

	std::atomic_uint_fast32_t linesPos; // Position for executing line movement
	std::atomic_uint_fast32_t linesWritePos; // Position where we write the next cached line move
	std::atomic_uint_fast32_t linesCount;      ///< Number of lines cached 0 = nothing to do.
    std::atomic<long> linesTicksCount;

	unsigned int moveCacheSize; // set on init

	int printMoveBufferWait;
	int minBufferedMoveTime;
	int maxBufferedMoveTime;



    std::vector<Path> lines;

	inline void previousPlannerIndex(unsigned int &p)
    {
        p = (p ? p-1 : moveCacheSize-1);
    }
	inline void nextPlannerIndex(unsigned int& p)
    {
        p = (p == moveCacheSize - 1 ? 0 : p + 1);
    }

	inline void removeCurrentLine()
    {
        linesTicksCount -= lines[linesPos].timeInTicks;
        linesPos++;
        if(linesPos>=moveCacheSize) linesPos=0;
        --linesCount;
    }

    inline bool isLinesBufferFilled()
    {
        return linesTicksCount >= (F_CPU/1000)*maxBufferedMoveTime;
    }
	
	std::mutex line_mutex;
	std::condition_variable lineAvailable;
	
	std::thread runningThread;
	bool stop;
	
	PruTimer pru;
	void recomputeParameters();
	void run();

public:
	
	/**
	 * @brief Create a new path planner that is used to compute paths parameters and send it to the PRU for execution
	 * @details Create a new path planner that is used to compute paths parameters and send it to the PRU for execution
	 * @param cacheSize Size of the movement planner cache
	 */
	PathPlanner(unsigned int cacheSize);
	
	/**
	 * @brief  Init the internal PRU co-processors
	 * @details Init the internal PRU co-processors with the provided firmware
	 * 
	 * @param firmware_stepper The firmware for the stepper step generation, will be executed on PRU0
	 * @param firmware_endstops The firmware for the endstop checks, will be executed on PRU1
	 * 
	 * @return true in case of success, false otherwise.
	 */
	bool initPRU(const std::string& firmware_stepper, const std::string& firmware_endstops) {
		return pru.initPRU(firmware_stepper, firmware_endstops);
	}

	/**
	 * @brief Sets a syncronization point to be signaled by the PRU
	 * @details Sets an option on the last queued move/segment to send a syncronization event when
	 * encountered by the PRU
	 *
	 * @ param isBlocking Causes the PRU to suspend once the sync event occurs.
         * @ returns true if the sync event was successfully added.  False on failure.
	 */
	bool queueSyncEvent(bool isBlocking = true);

	/**
	 * @brief Blocks until a pending Sync event is encountered.
	 * @details Monitors the PRU for a sync event, then returns. Note that the event must be manually
	 * cleared before processing can continue.
	 *
	 */
	int waitUntilSyncEvent();

	/**
	 * @brief Clears a SINGLE sync event and restores normal operation of the stepper PRU
	 * @details Clears the Sync event generated by the PRU then returns. 
	 * Note that a pending event must be manually cleared before processing can continue.
	 *
	 */
	void clearSyncEvent();

	/**
	 * @brief Queue a line move for execution
	 * @details Queue a line move execution in the path planner. Note that the path planner 
	 * has no internal state in term of printer head position. Therefore you have 
	 * to pass the correct start and end position everytime.
	 * 
	 * The coordinates unit is in meters. As a general rule, every public method of this class use SI units.
	 * 
	 * @param startPos The starting position of the path in meters
	 * @param endPos The end position of the path in meters
	 * @param speed The feedrate (aka speed) of the move in m/s
         * @param cancelable flags the move as cancelable.
         * @param optimize Wait for additional commands to fill the buffer, to optimize speed.
	 */
	void queueMove(FLOAT_T startPos[NUM_AXIS], FLOAT_T endPos[NUM_AXIS], FLOAT_T speed, bool cancelable, bool optimize=true );

	/**
	 * @brief Queue a batch of line moves for execution
	 * @details Queue a batch of line moves for execution in the path planner. Note that the path planner 
	 * has no internal state in term of printer head position. Therefore you have 
	 * to pass the correct start and end position everytime.
	 * 
	 * The coordinates unit is in meters. As a general rule, every public method of this class use SI units.
	 * 
	 * @param numSegments number of line moves being queued
	 * @param segments Block of FLOAT_T* line segments with startPos, endPos, and speed, for each segment
	 * @param cancelable flags the entire group of moves as cancelable.
	 * @param optimize Waits upto PRINT_MOVE_BUFFER_WAIT to perform speed optimization on an entire group of moves.
	 */
	void queueBatchMove(FLOAT_T* batchData, int batchSize, FLOAT_T speed, bool cancelable, bool optimize=true);
	
	/**
	 * @brief Run the path planner thread
	 * @details Run the path planner thread that is in charge to compute the different delays and submit it to the PRU for execution.
	 */
	void runThread();

	/**
	 * @brief Stop the path planner thread
	 * @details Stop the path planner thread and optionnaly wait until it is stopped before returning.
	 * 
	 * @param join If true, the method does not return until the thread is effectively stopped.
	 */
	void stopThread(bool join);
	

	/**
	 * @brief Wait until all queued move are finished to be executed
	 * @details Wait until all queued move are finished to be executed
	 */
	void waitUntilFinished();


	/**
	 * @brief Set current extruder number used
	 * @details Set extruder number used starting with ext 0
	 * 
	 * @param extNr The extruder number
	 */
    void setExtruder(int extNr);
	
	/**
	 * @brief Return the extruder extNr
	 * @details Return the extruder extNr in order to configure it.
	 * @warning You have to call setExtruder() again if you modify the currently used extruder.
	 * @param extNr The extruder number to get
	 * @return The extruder corresponding to extNr
	 */
	inline Extruder& getExtruder(int extNr) {
		assert(extNr<NUM_EXTRUDER);
		return extruders[extNr];
	}

	/**
	 * @brief Set the print move buffer wait time
	 * @details Time to wait before processing a print command if the buffer is not full enough, expressed in milliseconds.
     * Increasing this time will reduce the slow downs due to the path planner not having enough path in the buffer
     * but it will increase the startup time of the print.
     * @param dt time to wait before processing commands
     */
    void setPrintMoveBufferWait(int dt);


    /**
     * @brief Set the minimum buffered move time
     * @details Minimum of move buffered in the PRU (in term of move time in milliseconds) before we stop sending moves to the PRU.
     * Should be as low as possible so that we can keep some moves in the PathPlanner buffer for proper speed computations
     * @param dt minimum buffered move time
     */
    void setMinBufferedMoveTime(int dt);

    /**
    * @brief Set the maximum buffered move time
    * @details Time to wait before processing a print command if the buffer is not full enough, expressed in milliseconds.
    * Increasing this time will reduce the slow downs due to the path planner not having enough path in the buffer
    * but it will increase the startup time of the print.
    * @param dt maximum buffered move time
    */
	void setMaxBufferedMoveTime(int dt);

	/**
	 * @brief Set the maximum feedrates of the different axis X,Y,Z
	 * @details Set the maximum feedrates of the different axis in m/s
	 * 
	 * @param rates The feedrate for each of the axis, consisting of a NUM_AXIS length array.
	 */
	void setMaxFeedrates(FLOAT_T rates[NUM_MOVING_AXIS]);


	/**
	 * @brief Set the number of steps required to move each axis by 1 meter
	 * @details Set the number of steps required to move each axis by 1 meter
	 * 
	 * @param stepPerM the number of steps required to move each axis by 1 meter, consisting of a NUM_AXIS length array.
	 */
	void setAxisStepsPerMeter(unsigned long stepPerM[NUM_MOVING_AXIS]);

	/**
	 * @brief Set the max acceleration for printing moves
	 * @details Set the max acceleration for moves when the extruder is activated
	 * 
	 * @param accel The acceleration in m/s^2
	 */
	void setPrintAcceleration(FLOAT_T accel[NUM_MOVING_AXIS]);

	/**
	 * @brief Set the max acceleration for travel moves
	 * @details Set the max acceleration for moves when the extruder is not activated (i.e. not printing)
	 * 
	 * @param accel The acceleration in m/s^2
	 */
	void setTravelAcceleration(FLOAT_T accel[NUM_MOVING_AXIS]);

	/**
	 * @brief Set the maximum speed that can be used when in a corner
	 * @details The jerk determines your start speed and the maximum speed at the join of two segments.
	 * 
	 * Its unit is m/s. 
	 * 
	 * If the printer is standing still, the start speed is jerk/2. At the join of two segments, the speed 
	 * difference is limited to the jerk value.
	 * 
	 * Examples:
	 * 
	 * For all examples jerk is assumed as 40.
	 * 
	 * Segment 1: vx = 50, vy = 0
	 * Segment 2: vx = 0, vy = 50
	 * v_diff = sqrt((50-0)^2+(0-50)^2) = 70.71
	 * v_diff > jerk => vx_1 = vy_2 = jerk/v_diff*vx_1 = 40/70.71*50 = 28.3 mm/s at the join
	 * 
	 * Segment 1: vx = 50, vy = 0
	 * Segment 2: vx = 35.36, vy = 35.36
	 * v_diff = sqrt((50-35.36)^2+(0-35.36)^2) = 38.27 < jerk
	 * Corner can be printed with full speed of 50 mm/s
	 *
	 * @param maxJerk The maximum jerk for X and Y axis in m/s
	 * @param maxZJerk The maximum jerk for Z axis in m/s
	 */
	void setMaxJerk(FLOAT_T maxJerk, FLOAT_T maxZJerk);
	
	void suspend() {
		pru.suspend();
	}
	
	void resume() {
		pru.resume();
	}

	
	/**
	 * @brief Set current drive system (Cartesian, H-belt, CoreXY, Delta)
	 * @details Set current drive system (Cartesian, H-belt, CoreXY, Delta)
	 * 
	 * @param driveSystem the drive system used
	 */
    void setDriveSystem(int driveSystem);

	void reset();
	
	virtual ~PathPlanner();

};

#endif /* defined(__PathPlanner__PathPlanner__) */
