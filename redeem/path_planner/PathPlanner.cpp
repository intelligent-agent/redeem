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

#include "PathPlanner.h"
#include <cmath>
#include <assert.h>
#include <thread>

#ifdef BUILD_PYTHON_EXT
#include <Python.h>
#endif

void Extruder::setMaxFeedrate(FLOAT_T rate){
	//here the target unit is mm/s, we need to convert from m/s to mm/s
	maxFeedrate = rate*1000;
}

void Extruder::setPrintAcceleration(FLOAT_T accel){
	//here the target unit is mm/s^2, we need to convert from m/s^2 to mm/s^2
	maxAccelerationMMPerSquareSecond = accel*1000;
	recomputeParameters();
}

void Extruder::setTravelAcceleration(FLOAT_T accel){
	//here the target unit is mm/s^2, we need to convert from m/s^2 to mm/s^2
	maxTravelAccelerationMMPerSquareSecond = accel*1000;
	recomputeParameters();
}

void Extruder::setAxisStepsPerMeter(unsigned long stepPerM) {
	//here the target unit is step / mm, we need to convert from step / m to step / mm
	axisStepsPerMM = stepPerM/1000;
	recomputeParameters();
}

void Extruder::setMaxStartFeedrate(FLOAT_T f) {
	maxStartFeedrate = f*1000;
}

void Extruder::recomputeParameters() {
	invAxisStepsPerMM=1.0/axisStepsPerMM;
	/** Acceleration in steps/s^2 in printing mode.*/
	maxPrintAccelerationStepsPerSquareSecond =  maxAccelerationMMPerSquareSecond * (axisStepsPerMM);
	/** Acceleration in steps/s^2 in movement mode.*/
	maxTravelAccelerationStepsPerSquareSecond = maxTravelAccelerationMMPerSquareSecond * (axisStepsPerMM);
}



void PathPlanner::setExtruder(int extNr){
	assert(extNr<NUM_EXTRUDER);
	
    currentExtruder = extruders+extNr;
	
	maxFeedrate[E_AXIS] = currentExtruder->maxFeedrate;
	maxPrintAccelerationStepsPerSquareSecond[E_AXIS] = currentExtruder->maxPrintAccelerationStepsPerSquareSecond;
	maxTravelAccelerationStepsPerSquareSecond[E_AXIS] = currentExtruder->maxTravelAccelerationStepsPerSquareSecond;
	maxAccelerationMMPerSquareSecond[E_AXIS] = currentExtruder->maxAccelerationMMPerSquareSecond;
	maxTravelAccelerationMMPerSquareSecond[E_AXIS] = currentExtruder->maxTravelAccelerationMMPerSquareSecond;
	invAxisStepsPerMM[E_AXIS] = currentExtruder->invAxisStepsPerMM;
	axisStepsPerMM[E_AXIS] = currentExtruder->axisStepsPerMM;
}

void PathPlanner::setPrintMoveBufferWait(int dt) {
    printMoveBufferWait = dt;
}

void PathPlanner::setMinBufferedMoveTime(int dt) {
    minBufferedMoveTime = dt;
}

void PathPlanner::setMaxBufferedMoveTime(int dt) {
    maxBufferedMoveTime = dt;
}

void PathPlanner::setMaxFeedrates(FLOAT_T rates[NUM_MOVING_AXIS]){
	//here the target unit is mm/s, we need to convert from m/s to mm/s
	for(int i=0;i<NUM_MOVING_AXIS;i++) {
		maxFeedrate[i] = rates[i]*1000;
	}
}

void PathPlanner::setPrintAcceleration(FLOAT_T accel[NUM_MOVING_AXIS]){
	//here the target unit is mm/s^2, we need to convert from m/s^2 to mm/s^2
	for(int i=0;i<NUM_MOVING_AXIS;i++) {
		maxAccelerationMMPerSquareSecond[i] = accel[i]*1000;
	}
	recomputeParameters();
}

void PathPlanner::setTravelAcceleration(FLOAT_T accel[NUM_MOVING_AXIS]){
	//here the target unit is mm/s^2, we need to convert from m/s^2 to mm/s^2
	for(int i=0;i<NUM_MOVING_AXIS;i++) {
		maxTravelAccelerationMMPerSquareSecond[i] = accel[i]*1000;
	}
	recomputeParameters();
}

void PathPlanner::setMaxJerk(FLOAT_T maxJerk, FLOAT_T maxZJerk){
	this->maxJerk = maxJerk * 1000;
	this->maxZJerk = maxZJerk * 1000;
}

void PathPlanner::setAxisStepsPerMeter(unsigned long stepPerM[NUM_MOVING_AXIS]) {
	//here the target unit is step / mm, we need to convert from step / m to step / mm
	for(int i=0;i<NUM_MOVING_AXIS;i++) {
		axisStepsPerMM[i] = stepPerM[i]/1000;
	}
	recomputeParameters();
}

void PathPlanner::recomputeParameters() {
	for(uint8_t i=0; i<NUM_MOVING_AXIS; i++)
    {
		invAxisStepsPerMM[i]=1.0/axisStepsPerMM[i];
        /** Acceleration in steps/s^2 in printing mode.*/
        maxPrintAccelerationStepsPerSquareSecond[i] =  maxAccelerationMMPerSquareSecond[i] * (axisStepsPerMM[i]);
        /** Acceleration in steps/s^2 in movement mode.*/
        maxTravelAccelerationStepsPerSquareSecond[i] = maxTravelAccelerationMMPerSquareSecond[i] * (axisStepsPerMM[i]);
    }
	
	
	FLOAT_T accel = std::max(maxAccelerationMMPerSquareSecond[X_AXIS],maxTravelAccelerationMMPerSquareSecond[X_AXIS]);
    minimumSpeed = accel*sqrt(2.0f/(axisStepsPerMM[X_AXIS]*accel));
    accel = std::max(maxAccelerationMMPerSquareSecond[Z_AXIS],maxTravelAccelerationMMPerSquareSecond[Z_AXIS]);
    minimumZSpeed = accel*sqrt(2.0f/(axisStepsPerMM[Z_AXIS]*accel));
	
}

void PathPlanner::setDriveSystem(int driveSystem){
    this->driveSystem = driveSystem;
}	


PathPlanner::PathPlanner(unsigned int cacheSize) {
	linesPos = 0;
	linesWritePos = 0;

	moveCacheSize = cacheSize;
	lines.resize(moveCacheSize);

	//Default settings for debug mode
	
	static_assert(NUM_EXTRUDER>0,"Invalid number of extruder");
	
	for(unsigned int i=0;i<NUM_EXTRUDER;i++) {
		extruders[i].setStepperCommandPosition(i+3);
	}
	
	maxJerk =20;
	maxZJerk= 0.3;

	printMoveBufferWait = 250;
	minBufferedMoveTime = 100;
	maxBufferedMoveTime = 6*printMoveBufferWait;


	recomputeParameters();
	
	linesCount = 0;
	linesTicksCount = 0;

	currentExtruder = &extruders[0];
    driveSystem = 0; 
	
	stop = false;
}

bool PathPlanner::queueSyncEvent(bool isBlocking /* = true */)
{
#ifdef BUILD_PYTHON_EXT
	PyThreadState *_save; 
	_save = PyEval_SaveThread();
#endif
	// If the move command buffer isn't empty, make the last line a sync event
	{	
		std::unique_lock<std::mutex> lk(line_mutex);
		if(linesCount > 0)
		{
			unsigned int lastLine = (linesWritePos == 0) ? moveCacheSize - 1 : linesWritePos - 1;

			Path *p = &lines[lastLine];
			p->setSyncEvent(isBlocking);
#ifdef BUILD_PYTHON_EXT
			PyEval_RestoreThread(_save);
#endif
			return true;
		}
	}

#ifdef BUILD_PYTHON_EXT
	PyEval_RestoreThread(_save);
#endif
	return false;	// If the move command buffer is completly empty, it's too late.

}

int PathPlanner::waitUntilSyncEvent()
{
    int ret;
#ifdef BUILD_PYTHON_EXT
	PyThreadState *_save; 
	_save = PyEval_SaveThread();
#endif

	// Wait for a sync event on the stepper PRU
	ret = pru.waitUntilSync();

#ifdef BUILD_PYTHON_EXT
	PyEval_RestoreThread(_save);
#endif
    return ret;
}
                     
void PathPlanner::clearSyncEvent()
{

#ifdef BUILD_PYTHON_EXT
	PyThreadState *_save; 
	_save = PyEval_SaveThread();
#endif

	// Clear the sync event on the stepper PRU and resume operation.
	pru.resume();


#ifdef BUILD_PYTHON_EXT
	PyEval_RestoreThread(_save);
#endif

}

void PathPlanner::queueBatchMove(FLOAT_T* batchData, int batchSize, FLOAT_T speed, bool cancelable, bool optimize /* = true */) {
    FLOAT_T axis_diff[NUM_AXIS]; // Axis movement in mm
	

#ifdef BUILD_PYTHON_EXT
	PyThreadState *_save; 
	_save = PyEval_SaveThread();
#endif
        int numSegments = batchSize / (2 * NUM_AXIS);
	//LOG( "Batching " << numSegments << " segments." << std::endl);

	unsigned int linesQueued = 0;
	unsigned int linesCacheRemaining = 0;
    long linesTicksRemaining = 0;
    long linesTicksQueued = 0;

	// Process each segment
	for(int segment_index = 0; segment_index < numSegments; segment_index++)
	{
               
		// wait for the worker
		if(linesCacheRemaining == 0 || linesTicksRemaining == 0)
		{
			std::unique_lock<std::mutex> lk(line_mutex);
			//LOG( "Waiting for free move command space... Current: " << moveCacheSize - linesCount << std::endl);
			lineAvailable.wait(lk, [this]{
                return 
                    stop || 
                    (linesCount < moveCacheSize && !isLinesBufferFilled());
            });
			linesCacheRemaining = moveCacheSize - linesCount;
            linesTicksRemaining = maxBufferedMoveTime - linesTicksCount;
		}
	
		if(stop)
		{
	
#ifdef BUILD_PYTHON_EXT
		        PyEval_RestoreThread(_save);
#endif
			LOG( "Stopped/aborted/Cancelled while waiting for free move command space. linesCount: " << linesCount << std::endl);
		        return;
		}

		Path *p = &lines[linesWritePos];
                // Batch is packed into memory as a continious array.
		// SSSSEEEESSSSEEEESSSSEEEESSSSEEEE
		// ^0      ^8      ^16     ^24 (x sizeof(FLOAT_T))
		memcpy(p->startPos, /* startPos */ &batchData[segment_index * 2 * NUM_AXIS], sizeof(FLOAT_T)*NUM_AXIS);
		memcpy(p->endPos, /* endPos */ &batchData[segment_index * 2 * NUM_AXIS + NUM_AXIS], sizeof(FLOAT_T)*NUM_AXIS);

		
		//Convert meters to mm
		for(uint8_t axis=0; axis < NUM_AXIS; axis++)
		{
			p->startPos[axis]*=1000.0;
			p->endPos[axis]*=1000.0;
		}
		
		p->speed = speed*1000; //Speed is in m/s
		p->joinFlags = 0;
		p->flags = 0;
		p->setCancelable(cancelable);
		
		p->setWaitMS(optimize ? printMoveBufferWait : 0);
	
		p->dir = 0;
		
		//Find direction
		for(uint8_t axis=0; axis < NUM_AXIS; axis++)
		{
			p->startPos[axis] = ceil(p->startPos[axis]*axisStepsPerMM[axis]);
			p->endPos[axis] = ceil(p->endPos[axis]*axisStepsPerMM[axis]);
			
		        if((p->delta[axis]=p->endPos[axis]-p->startPos[axis])>=0)
				p->setPositiveDirectionForAxis(axis);
			else
				p->delta[axis] = -p->delta[axis];
			
			axis_diff[axis] = p->delta[axis] * invAxisStepsPerMM[axis];
			if(p->delta[axis]) 
				p->setMoveOfAxis(axis);
			
		}
		
		if(p->isNoMove())
		{
			LOG( "Warning: no move path" << std::endl);
			continue; // No steps included
		}
		
		//LOG( "Warning: Doing the breshnam thing" << std::endl);
	
		//Define variables that are needed for the Bresenham algorithm. Please note that  Z is not currently included in the Bresenham algorithm.
		if(p->delta[Y_AXIS] > p->delta[X_AXIS] && p->delta[Y_AXIS] > p->delta[Z_AXIS] && p->delta[Y_AXIS] > p->delta[E_AXIS])
			p->primaryAxis = Y_AXIS;
		else if (p->delta[X_AXIS] > p->delta[Z_AXIS] && p->delta[X_AXIS] > p->delta[E_AXIS])
			p->primaryAxis = X_AXIS;
		else if (p->delta[Z_AXIS] > p->delta[E_AXIS])
			p->primaryAxis = Z_AXIS;
		else
			p->primaryAxis = E_AXIS;
		
		p->stepsRemaining = p->delta[p->primaryAxis];
	    
		if(p->isXYZMove())
		{
			FLOAT_T xydist2 = axis_diff[X_AXIS] * axis_diff[X_AXIS] + axis_diff[Y_AXIS] * axis_diff[Y_AXIS];
			if(p->isZMove())
				p->distance = std::max((FLOAT_T)sqrt(xydist2 + axis_diff[Z_AXIS] * axis_diff[Z_AXIS]),(FLOAT_T)fabs(axis_diff[E_AXIS]));
			else
				p->distance = std::max((FLOAT_T)sqrt(xydist2),(FLOAT_T)fabs(axis_diff[E_AXIS]));
		}
		else
			p->distance = fabs(axis_diff[E_AXIS]);
		
		calculateMove(p,axis_diff);
		updateTrapezoids();

		linesWritePos++;

		linesQueued++;
		linesCacheRemaining--;

        linesTicksQueued += p->timeInTicks;
        linesTicksRemaining -= p->timeInTicks;
		
		if(linesWritePos>=moveCacheSize)
			linesWritePos = 0;
		
		// Notify the run() thread to work
        //   when queue is full, or at the end of this batch.
		if((linesCacheRemaining == 0) || 
            ((segment_index + 1) == numSegments) ||
            linesTicksRemaining <= 0)	
		{
			{
                std::lock_guard<std::mutex> lk(line_mutex);
                linesCount += linesQueued;
                linesTicksCount += linesTicksQueued;
			}
			linesQueued = 0;
            linesTicksQueued = 0;
			lineAvailable.notify_all();
		}
		//LOG( "Line finished (" << linesQueued << "lines ready)." << std::endl);
	}

	//LOG( "End batch queuing move command" << std::endl);

#ifdef BUILD_PYTHON_EXT
	PyEval_RestoreThread(_save);
#endif

}


void PathPlanner::queueMove(FLOAT_T startPos[NUM_AXIS],FLOAT_T endPos[NUM_AXIS],FLOAT_T speed, bool cancelable, bool optimize) {

	// This seems redundant...
	FLOAT_T temp[NUM_AXIS * 2];

	memcpy(temp, startPos, sizeof(FLOAT_T)*NUM_AXIS);
	memcpy(&temp[NUM_AXIS], endPos, sizeof(FLOAT_T)*NUM_AXIS);
	
	queueBatchMove( temp, NUM_AXIS*2, speed, cancelable, optimize);

}

FLOAT_T PathPlanner::safeSpeed(Path* p)
{
    FLOAT_T safe = maxJerk * 0.5;
	
    if(p->isZMove())
    {
        if(p->primaryAxis == Z_AXIS)
        {
            safe = maxZJerk*0.5*p->fullSpeed/fabs(p->speedZ);
        }
        else if(fabs(p->speedZ) > maxZJerk * 0.5)
            safe = std::min(safe,(FLOAT_T)(maxZJerk * 0.5 * p->fullSpeed / fabs(p->speedZ)));
    }
	
    if(p->isEMove())
    {
        if(p->isXYZMove())
            safe = std::min(safe,(FLOAT_T)(0.5*currentExtruder->maxStartFeedrate*p->fullSpeed/fabs(p->speedE)));
        else
            safe = 0.5*currentExtruder->maxStartFeedrate; // This is a retraction move
    }
    if(p->primaryAxis == X_AXIS || p->primaryAxis == Y_AXIS) // enforce minimum speed for numerical stability of explicit speed integration
        safe = std::max(minimumSpeed,safe);
    else if(p->primaryAxis == Z_AXIS)
    {
        safe = std::max(minimumZSpeed,safe);
    }
    return std::min(safe,p->fullSpeed);
}

void PathPlanner::calculateMove(Path* p,FLOAT_T axis_diff[NUM_AXIS])
{
    unsigned int axisInterval[NUM_AXIS];
	FLOAT_T timeForMove = (FLOAT_T)(F_CPU)*p->distance / (p->isXOrYMove() ? std::max(minimumSpeed,p->speed): p->speed); // time is in ticks
	
/*
	 #define MOVE_CACHE_LOW 512
	 if(linesCount < MOVE_CACHE_LOW)   // Limit speed to keep cache full.
	 {
	 #define LOW_TICKS_PER_MOVE F_CPU/50
	 
	 timeForMove += (3 * (LOW_TICKS_PER_MOVE-timeForMove)) / (linesCount+1); // Increase time if queue gets empty. Add more time if queue gets smaller.
	 }
*/

	
    p->timeInTicks = timeForMove;
	
    // Compute the solwest allowed interval (ticks/step), so maximum feedrate is not violated
    unsigned int limitInterval = timeForMove/p->stepsRemaining; // until not violated by other constraints it is your target speed
    if(p->isXMove())
    {
        axisInterval[X_AXIS] = fabs(axis_diff[X_AXIS]) * F_CPU / (maxFeedrate[X_AXIS] * p->stepsRemaining); // mm*ticks/s/(mm/s*steps) = ticks/step
        limitInterval = std::max(axisInterval[X_AXIS],limitInterval);
    }
    else axisInterval[X_AXIS] = 0;
    if(p->isYMove())
    {
        axisInterval[Y_AXIS] = fabs(axis_diff[Y_AXIS])*F_CPU/(maxFeedrate[Y_AXIS]*p->stepsRemaining);
        limitInterval = std::max(axisInterval[Y_AXIS],limitInterval);
    }
    else axisInterval[Y_AXIS] = 0;
    if(p->isZMove())   // normally no move in z direction
    {
        axisInterval[Z_AXIS] = fabs((FLOAT_T)axis_diff[Z_AXIS])*(FLOAT_T)F_CPU/(FLOAT_T)(maxFeedrate[Z_AXIS]*p->stepsRemaining); // must prevent overflow!
        limitInterval = std::max(axisInterval[Z_AXIS],limitInterval);
    }
    else axisInterval[Z_AXIS] = 0;
    if(p->isEMove())
    {
        axisInterval[E_AXIS] = fabs(axis_diff[E_AXIS])*F_CPU/(maxFeedrate[E_AXIS]*p->stepsRemaining);
        limitInterval = std::max(axisInterval[E_AXIS],limitInterval);
    }
    else axisInterval[E_AXIS] = 0;
	
    p->fullInterval = limitInterval; // = limitInterval>LIMIT_INTERVAL ? limitInterval : LIMIT_INTERVAL; // This is our target speed
	
    // new time at full speed = limitInterval*p->stepsRemaining [ticks]
    timeForMove = (FLOAT_T)limitInterval * (FLOAT_T)p->stepsRemaining; // for large z-distance this overflows with long computation
    FLOAT_T inv_time_s = (FLOAT_T)F_CPU / timeForMove;
    if(p->isXMove())
    {
        axisInterval[X_AXIS] = timeForMove / p->delta[X_AXIS];
        p->speedX = axis_diff[X_AXIS] * inv_time_s;
        if(p->isXNegativeMove()) p->speedX = -p->speedX;
    }
    else p->speedX = 0;
    if(p->isYMove())
    {
        axisInterval[Y_AXIS] = timeForMove/p->delta[Y_AXIS];
        p->speedY = axis_diff[Y_AXIS] * inv_time_s;
        if(p->isYNegativeMove()) p->speedY = -p->speedY;
    }
    else p->speedY = 0;
    if(p->isZMove())
    {
        axisInterval[Z_AXIS] = timeForMove/p->delta[Z_AXIS];
        p->speedZ = axis_diff[Z_AXIS] * inv_time_s;
        if(p->isZNegativeMove()) p->speedZ = -p->speedZ;
    }
    else p->speedZ = 0;
    if(p->isEMove())
    {
        axisInterval[E_AXIS] = timeForMove/p->delta[E_AXIS];
        p->speedE = axis_diff[E_AXIS] * inv_time_s;
        if(p->isENegativeMove()) p->speedE = -p->speedE;
    }
	
    p->fullSpeed = p->distance * inv_time_s;
    //long interval = axis_interval[primary_axis]; // time for every step in ticks with full speed
    //If acceleration is enabled, do some Bresenham calculations depending on which axis will lead it.
	
    // slowest time to accelerate from v0 to limitInterval determines used acceleration
    // t = (v_end-v_start)/a
    FLOAT_T slowest_axis_plateau_time_repro = 1e15; // repro to reduce division Unit: 1/s
    unsigned long *accel = (p->isEPositiveMove() ?  maxPrintAccelerationStepsPerSquareSecond : maxTravelAccelerationStepsPerSquareSecond);
    for(uint8_t i=0; i < 4 ; i++)
    {
        if(p->isMoveOfAxis(i))
            // v = a * t => t = v/a = F_CPU/(c*a) => 1/t = c*a/F_CPU
            slowest_axis_plateau_time_repro = std::min(slowest_axis_plateau_time_repro,(FLOAT_T)axisInterval[i] * (FLOAT_T)accel[i]); //  steps/s^2 * step/tick  Ticks/s^2
    }
    // Errors for delta move are initialized in timer (except extruder)
    p->error[0] = p->error[1] = p->error[2] = p->delta[p->primaryAxis] >> 1;
    p->invFullSpeed = 1.0/p->fullSpeed;
    p->accelerationPrim = slowest_axis_plateau_time_repro / axisInterval[p->primaryAxis]; // a = v/t = F_CPU/(c*t): Steps/s^2
    //Now we can calculate the new primary axis acceleration, so that the slowest axis max acceleration is not violated
    p->fAcceleration = 262144.0*(FLOAT_T)p->accelerationPrim/F_CPU; // will overflow without FLOAT_T!
    p->accelerationDistance2 = 2.0*p->distance*slowest_axis_plateau_time_repro*p->fullSpeed/((FLOAT_T)F_CPU); // mm^2/s^2
    p->startSpeed = p->endSpeed = p->minSpeed = safeSpeed(p);
    // Can accelerate to full speed within the line
    if (p->startSpeed * p->startSpeed + p->accelerationDistance2 >= p->fullSpeed * p->fullSpeed)
        p->setNominalMove();
	
    p->vMax = F_CPU / p->fullInterval; // maximum steps per second, we can reach   
    // how much steps on primary axis do we need to reach target feedrate
    //p->plateauSteps = (long) (((FLOAT_T)p->acceleration *0.5f / slowest_axis_plateau_time_repro + p->vMin) *1.01f/slowest_axis_plateau_time_repro);
	
}

/** Update parameter used by updateTrapezoids
 
 Computes the acceleration/decelleration steps and advanced parameter associated.
 */
void Path::updateStepsParameter()
{
    if(areParameterUpToDate() || isWarmUp()) return;
    FLOAT_T startFactor = startSpeed * invFullSpeed;
    FLOAT_T endFactor   = endSpeed   * invFullSpeed;
    vStart = vMax * startFactor; //starting speed
    vEnd   = vMax * endFactor;
    uint64_t vmax2 = static_cast<uint64_t>(vMax) * static_cast<uint64_t>(vMax);
    accelSteps = (unsigned int)(((vmax2 - static_cast<uint64_t>(vStart) * static_cast<uint64_t>(vStart)) / (accelerationPrim<<1)) + 1); // Always add 1 for missing precision
    decelSteps = (unsigned int)(((vmax2 - static_cast<uint64_t>(vEnd) * static_cast<uint64_t>(vEnd))  /(accelerationPrim<<1)) + 1);
	
	
    if(accelSteps+decelSteps >= stepsRemaining)   // can't reach limit speed
    {
        unsigned int red = (accelSteps+decelSteps + 2 - stepsRemaining) >> 1;
        accelSteps = accelSteps-std::min(accelSteps,red);
        decelSteps = decelSteps-std::min(decelSteps,red);
    }
    setParameterUpToDate();
}




/**
 This is the path planner.
 
 It goes from the last entry and tries to increase the end speed of previous moves in a fashion that the maximum jerk
 is never exceeded. If a segment with reached maximum speed is met, the planner stops. Everything left from this
 is already optimal from previous updates.
 The first 2 entries in the queue are not checked. The first is the one that is already in print and the following will likely become active.
 
 The method is called before lines_count is increased!
 */
void PathPlanner::updateTrapezoids()
{
	unsigned int first = linesWritePos;
    Path *firstLine;
    Path *act = &lines[linesWritePos];
    //BEGIN_INTERRUPT_PROTECTED;
    unsigned int maxfirst = linesPos; // first non fixed segment

    // Search last fixed element
    while(first != maxfirst && !lines[first].isEndSpeedFixed())
        previousPlannerIndex(first);
    if(first != linesWritePos && lines[first].isEndSpeedFixed())
        nextPlannerIndex(first);
    if(first == linesWritePos)   // Nothing to plan
    {
        act->block();
        //ESCAPE_INTERRUPT_PROTECTED
        act->setStartSpeedFixed(true);
        act->updateStepsParameter();
        act->unblock();
        return;
    }
    // now we have at least one additional move for optimization
    // that is not a wait move
    // First is now the new element or the first element with non fixed end speed.
    // anyhow, the start speed of first is fixed
    firstLine = &lines[first];
    firstLine->block(); // don't let printer touch this or following segments during update
	// END_INTERRUPT_PROTECTED;
    unsigned int previousIndex = linesWritePos;
    previousPlannerIndex(previousIndex);
    Path *previous = &lines[previousIndex];
	
    // filters z-move<->not z-move
    if(driveSystem != 3 && ((previous->primaryAxis == Z_AXIS && act->primaryAxis != Z_AXIS) || (previous->primaryAxis != Z_AXIS && act->primaryAxis == Z_AXIS)) )
    {
        previous->setEndSpeedFixed(true);
        act->setStartSpeedFixed(true);
        act->updateStepsParameter();
        firstLine->unblock();
        return;
    }
	
	
    computeMaxJunctionSpeed(previous,act); // Set maximum junction speed if we have a real move before
    if(previous->isEOnlyMove() != act->isEOnlyMove())
    {
        previous->setEndSpeedFixed(true);
        act->setStartSpeedFixed(true);
        act->updateStepsParameter();
        firstLine->unblock();
        return;
    }
    backwardPlanner(linesWritePos,first);
    // Reduce speed to reachable speeds
    forwardPlanner(first);
	
    // Update precomputed data
    do
    {
        lines[first].updateStepsParameter();
        //BEGIN_INTERRUPT_PROTECTED;
        lines[first].unblock();  // Flying block to release next used segment as early as possible
        nextPlannerIndex(first);
        lines[first].block();
        //END_INTERRUPT_PROTECTED;
    }
    while(first!=linesWritePos);
    act->updateStepsParameter();
    act->unblock();
}

void PathPlanner::computeMaxJunctionSpeed(Path *previous,Path *current)
{
    // First we compute the normalized jerk for speed 1
    FLOAT_T dx = current->speedX-previous->speedX;
    FLOAT_T dy = current->speedY-previous->speedY;
    FLOAT_T dz = current->speedZ-previous->speedZ;
    FLOAT_T factor = 1;
    FLOAT_T jerk = sqrt(dx*dx + dy*dy + dz*dz);
    if(jerk>maxJerk)
        factor = maxJerk / jerk;
	
    if(driveSystem != 3 && ((previous->dir | current->dir) & 64))
    {
        if(dz>maxZJerk)
            factor = std::min(factor,maxZJerk / dz);
    }
	
    FLOAT_T eJerk = fabs(current->speedE - previous->speedE);
    if(eJerk > currentExtruder->maxStartFeedrate)
        factor = std::min(factor,currentExtruder->maxStartFeedrate / eJerk);
    previous->maxJunctionSpeed = std::min(previous->fullSpeed * factor,current->fullSpeed);
}



/**
 Compute the maximum speed from the last entered move.
 The backwards planner traverses the moves from last to first looking at deceleration. The RHS of the accelerate/decelerate ramp.
 
 start = last line inserted
 last = last element until we check
 */
void PathPlanner::backwardPlanner(unsigned int start, unsigned int last)
{
    Path *act = &lines[start],*previous;
    FLOAT_T lastJunctionSpeed = act->endSpeed; // Start always with safe speed
	
    //PREVIOUS_PLANNER_INDEX(last); // Last element is already fixed in start speed
    while(start != last)
    {
        previousPlannerIndex(start);
        previous = &lines[start];
		
        // Avoid speed calcs if we know we can accelerate within the line
        lastJunctionSpeed = (act->isNominalMove() ? act->fullSpeed : sqrt(lastJunctionSpeed * lastJunctionSpeed + act->accelerationDistance2)); // acceleration is acceleration*distance*2! What can be reached if we try?
        // If that speed is more that the maximum junction speed allowed then ...
        if(lastJunctionSpeed >= previous->maxJunctionSpeed)   // Limit is reached
        {
            // If the previous line's end speed has not been updated to maximum speed then do it now
            if(previous->endSpeed != previous->maxJunctionSpeed)
            {
                previous->invalidateParameter(); // Needs recomputation
                previous->endSpeed = std::max(previous->minSpeed,previous->maxJunctionSpeed); // possibly unneeded???
            }
            // If actual line start speed has not been updated to maximum speed then do it now
            if(act->startSpeed != previous->maxJunctionSpeed)
            {
                act->startSpeed = std::max(act->minSpeed,previous->maxJunctionSpeed); // possibly unneeded???
                act->invalidateParameter();
            }
            lastJunctionSpeed = previous->endSpeed;
        }
        else
        {
            // Block prev end and act start as calculated speed and recalculate plateau speeds (which could move the speed higher again)
            act->startSpeed = std::max(act->minSpeed,lastJunctionSpeed);
            lastJunctionSpeed = previous->endSpeed = std::max(lastJunctionSpeed,previous->minSpeed);
            previous->invalidateParameter();
            act->invalidateParameter();
        }
        act = previous;
    } // while loop
}

void PathPlanner::forwardPlanner(unsigned int first)
{
    Path *act;
    Path *next = &lines[first];
    FLOAT_T vmaxRight;
    FLOAT_T leftSpeed = next->startSpeed;
    while(first != linesWritePos)   // All except last segment, which has fixed end speed
    {
        act = next;
        nextPlannerIndex(first);
        next = &lines[first];
		
        // Avoid speed calcs if we know we can accelerate within the line.
        vmaxRight = (act->isNominalMove() ? act->fullSpeed : sqrt(leftSpeed * leftSpeed + act->accelerationDistance2));
        if(vmaxRight > act->endSpeed)   // Could be higher next run?
        {
            if(leftSpeed < act->minSpeed)
            {
                leftSpeed = act->minSpeed;
                act->endSpeed = sqrt(leftSpeed * leftSpeed + act->accelerationDistance2);
            }
            act->startSpeed = leftSpeed;
            next->startSpeed = leftSpeed = std::max(std::min(act->endSpeed,act->maxJunctionSpeed),next->minSpeed);
            if(act->endSpeed == act->maxJunctionSpeed)  // Full speed reached, don't compute again!
            {
                act->setEndSpeedFixed(true);
                next->setStartSpeedFixed(true);
            }
            act->invalidateParameter();
        }
        else     // We can accelerate full speed without reaching limit, which is as fast as possible. Fix it!
        {
            act->fixStartAndEndSpeed();
            act->invalidateParameter();
            if(act->minSpeed > leftSpeed)
            {
                leftSpeed = act->minSpeed;
                vmaxRight = sqrt(leftSpeed * leftSpeed + act->accelerationDistance2);
            }
            act->startSpeed = leftSpeed;
            act->endSpeed = std::max(act->minSpeed,vmaxRight);
            next->startSpeed = leftSpeed = std::max(std::min(act->endSpeed,act->maxJunctionSpeed),next->minSpeed);
            next->setStartSpeedFixed(true);
        }
    } // While
    next->startSpeed = std::max(next->minSpeed,leftSpeed); // This is the new segment, which is updated anyway, no extra flag needed.
}


void PathPlanner::runThread() {
	stop=false;
	
	pru.runThread();
	
	runningThread = std::thread([this]() {
		this->run();
	});
}

void PathPlanner::stopThread(bool join) {
#ifdef BUILD_PYTHON_EXT
    Py_BEGIN_ALLOW_THREADS
#endif
	pru.stopThread(join);
	
	stop=true;
	lineAvailable.notify_all();
	if(join && runningThread.joinable()) {
		runningThread.join();
	}
#ifdef BUILD_PYTHON_EXT
    Py_END_ALLOW_THREADS
#endif
}

PathPlanner::~PathPlanner() {
	if(runningThread.joinable()) {
		stopThread(true);
	}
}

void PathPlanner::waitUntilFinished() {

#ifdef BUILD_PYTHON_EXT
    Py_BEGIN_ALLOW_THREADS
#endif
    
	std::unique_lock<std::mutex> lk(line_mutex);
	lineAvailable.wait(lk, [this]{
        return linesCount==0 || stop;
    });
	
	//Wait for PruTimer then
	if(!stop) {
		pru.waitUntilFinished();
	}
#ifdef BUILD_PYTHON_EXT
    Py_END_ALLOW_THREADS
#endif
}

void PathPlanner::reset() {
	pru.reset();
}

void PathPlanner::run() {
	
	bool waitUntilFilledUp = true;
	
	while(!stop) {
		
		std::unique_lock<std::mutex> lk(line_mutex);
		
		lineAvailable.wait(lk, [this]{return linesCount>0 || stop;});
		
		Path* cur = &lines[linesPos];
		
		//If the buffer is half or more empty and the line to print is an optimized one , wait for 500 ms again so that we can get some other path in the path planner buffer, and we do that until the buffer is not anymore half empty.
		if(!isLinesBufferFilled() && cur->getWaitMS()>0 && waitUntilFilledUp) {
			unsigned lastCount = 0;
			//~ LOG("Waiting for buffer to fill up... " << linesCount  << " lines pending " << lastCount << std::endl);
			do {
				lastCount = linesCount;
				
				lineAvailable.wait_for(lk,  std::chrono::milliseconds(printMoveBufferWait), [this,lastCount]{return linesCount>lastCount || stop;});
				
			} while(lastCount<linesCount && linesCount<moveCacheSize && !stop);
			//~ LOG("Done waiting for buffer to fill up... " << linesCount  << " lines ready. " << lastCount << std::endl);
			
			waitUntilFilledUp = false;
		}
		
		//The buffer is empty, we enable again the "wait until buffer is enough full" timing procedure.
		if(linesCount<=1) {
			waitUntilFilledUp = true;
			LOG("### Move Command Buffer Empty ###" << std::endl);

		}
		
		
		lk.unlock();
		
		if(!linesCount || stop){
			continue;
		}
		
		
		
		
		long cur_errupd=0;
		uint8_t directionMask = 0; //0b000HEZYX
		uint8_t cancellableMask;
		unsigned long vMaxReached;
        unsigned long timer_accel = 0;
		unsigned long timer_decel = 0;
		
		if(cur->isBlocked())   // This step is in computation - shouldn't happen
		{
			cur = NULL;
			LOG( "Path planner thread: path " <<  std::dec << linesPos<< " is blocked, waiting... " << std::endl);
			std::this_thread::sleep_for( std::chrono::milliseconds(100) );
			continue;
		}
		
		//Only enable axis that are moving. If the axis doesn't need to move then it can stay disabled depending on configuration.
		cur->fixStartAndEndSpeed();
		cur_errupd = cur->delta[cur->primaryAxis];
		if(!cur->areParameterUpToDate())  // should never happen, but with bad timings???
		{
            LOG( "Path planner thread: Need to update paramters! This should not happen!" << std::endl);
			cur->updateStepsParameter();
		}
		
		vMaxReached = cur->vStart;

        // reset commands buffer every time
        cur->commands.clear();
        cur->commands.resize(cur->stepsRemaining);

		//Determine direction of movement,check if endstop was hit
		directionMask|=((uint8_t)cur->isXPositiveMove() << X_AXIS);
		directionMask|=((uint8_t)cur->isYPositiveMove() << Y_AXIS);
		directionMask|=((uint8_t)cur->isZPositiveMove() << Z_AXIS);
		directionMask|=((uint8_t)(cur->isEPositiveMove() ^ currentExtruder->directionInverted) << currentExtruder->stepperCommandPosition);
		
		cancellableMask = 0;
		
		if(cur->isCancelable()) {
			cancellableMask|=((uint8_t)cur->isXMove() << X_AXIS);
			cancellableMask|=((uint8_t)cur->isYMove() << Y_AXIS);
			cancellableMask|=((uint8_t)cur->isZMove() << Z_AXIS);
			cancellableMask|=((uint8_t)cur->isEMove() << currentExtruder->stepperCommandPosition);
		}
		
		assert(cur);
		assert(cur->commands);
		
		
		
		for(unsigned int stepNumber=0; stepNumber<cur->stepsRemaining; stepNumber++){
			SteppersCommand& cmd = cur->commands.at(stepNumber);
			cmd.direction = directionMask;
			cmd.cancellableMask = cancellableMask;
			
			if((stepNumber == cur->stepsRemaining - 1) && cur->isSyncEvent())
			{
				if(cur->isSyncWaitEvent())
					cmd.options = STEPPER_COMMAND_OPTION_SYNCWAIT_EVENT;
				else
					cmd.options = STEPPER_COMMAND_OPTION_SYNC_EVENT;
			}
			else 
				cmd.options = 0;

			cmd.step = 0;
			if(cur->isEMove())
			{
				if((cur->error[E_AXIS] -= cur->delta[E_AXIS]) < 0)
				{
					cmd.step |= (1 << currentExtruder->stepperCommandPosition);
					cur->error[E_AXIS] += cur_errupd;
				}
			}
			if(cur->isXMove())
			{
				if((cur->error[X_AXIS] -= cur->delta[X_AXIS]) < 0)
				{
					cmd.step |= (1 << X_AXIS);
					cur->error[X_AXIS] += cur_errupd;
				}
			}
			if(cur->isYMove())
			{
				if((cur->error[Y_AXIS] -= cur->delta[Y_AXIS]) < 0)
				{
					cmd.step |= (1 << Y_AXIS);
					cur->error[Y_AXIS] += cur_errupd;
				}
			}
			
			if(cur->isZMove())
			{
				if((cur->error[Z_AXIS] -= cur->delta[Z_AXIS]) < 0)
				{
					cmd.step |= (1 << Z_AXIS);
					cur->error[Z_AXIS] += cur_errupd;
				}
			}
			
#define ComputeV(timer,accel)  (((timer>>8)*accel)>>10)
			
			unsigned long interval;
			
			//If acceleration is enabled on this move and we are in the acceleration segment, calculate the current interval
			if (cur->moveAccelerating(stepNumber))   // we are accelerating
			{
				vMaxReached = ComputeV(timer_accel,cur->fAcceleration)+cur->vStart;
				if(vMaxReached>cur->vMax) vMaxReached = cur->vMax;
				unsigned long v = vMaxReached;
				interval = F_CPU/(v);
				timer_accel+=interval;
			}
			else if (cur->moveDecelerating(stepNumber))     // time to slow down
			{
				unsigned long v = ComputeV(timer_decel,cur->fAcceleration);
				if (v > vMaxReached)   // if deceleration goes too far it can become too large
					v = cur->vEnd;
			 	else{
					v=vMaxReached - v;
					if (v < cur->vEnd)
                        v = cur->vEnd; // extra steps at the end of desceleration due to rounding erros
				}
				
				interval = F_CPU/(v);
				timer_decel += interval;
			}
			else // full speed reached
			{
				// constant speed reached
				interval = cur->fullInterval;
			}
			
			assert(interval < F_CPU*4);
			cmd.delay = (uint32_t)interval;
		} // stepsRemaining

		
		//LOG("Current move time " << pru.getTotalQueuedMovesTime() / (double) F_CPU << std::endl);
		
		//Wait until we need to push some lines so that the path planner can fill up
		pru.waitUntilLowMoveTime((F_CPU/1000)*minBufferedMoveTime); //in seconds
		
		//LOG( "Sending " << std::dec << linesPos << ", Start speed=" << cur->startSpeed << ", end speed="<<cur->endSpeed << ", nb steps = " << cur->stepsRemaining << std::endl);
		
		pru.push_block((uint8_t*)cur->commands.data(), sizeof(SteppersCommand)*cur->stepsRemaining, sizeof(SteppersCommand),linesPos,cur->timeInTicks);
		
		// LOG( "Done sending with " << std::dec << linesPos << std::endl);
		
		removeCurrentLine();
		
		lineAvailable.notify_all();
	}
}
