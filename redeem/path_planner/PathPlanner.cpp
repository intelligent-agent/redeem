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
#include <Python.h>

#define ComputeV(timer,accel)  (((timer>>8)*accel)>>10)
#define ComputeV2(timer,accel)  (((timer/256.0)*accel)/1024)

void PathPlanner::setPrintMoveBufferWait(int dt) {
    printMoveBufferWait = dt;
}

void PathPlanner::setMinBufferedMoveTime(int dt) {
    minBufferedMoveTime = dt;
}

void PathPlanner::setMaxBufferedMoveTime(int dt) {
    maxBufferedMoveTime = dt;
}

// Speeds / accels
void PathPlanner::setMaxSpeeds(FLOAT_T speeds[NUM_AXES]){
	for(int i=0;i<NUM_AXES;i++) {
		maxSpeeds[i] = speeds[i];
	}
}

void PathPlanner::setMinSpeeds(FLOAT_T speeds[NUM_AXES]){
    for(int i=0; i<NUM_AXES; i++){
        minSpeeds[i] = speeds[i];
    }
}

void PathPlanner::setAcceleration(FLOAT_T accel[NUM_AXES]){
	for(int i=0;i<NUM_AXES;i++) {
		maxAccelerationMPerSquareSecond[i] = accel[i];
	}
	recomputeParameters();
}

void PathPlanner::setJerks(FLOAT_T jerks[NUM_AXES]){
	for(int i=0;i<NUM_AXES;i++) {
		maxJerks[i] = jerks[i];
	}
}

void PathPlanner::setAxisStepsPerMeter(FLOAT_T stepPerM[NUM_AXES]) {
	for(int i=0;i<NUM_AXES;i++) {
		axisStepsPerM[i] = stepPerM[i];
	}
	recomputeParameters();
}

void PathPlanner::recomputeParameters() {
	for(int i=0; i<NUM_AXES; i++){
        /** Acceleration in steps/s^2 in printing mode.*/
        maxAccelerationStepsPerSquareSecond[i] =  maxAccelerationMPerSquareSecond[i] * axisStepsPerM[i];
    }
}

PathPlanner::PathPlanner(unsigned int cacheSize) {
	linesPos = 0;
	linesWritePos = 0;
    LOG( "PathPlanner " << std::endl);
	moveCacheSize = cacheSize;
	lines.resize(moveCacheSize);
	printMoveBufferWait = 250;
	minBufferedMoveTime = 100;
	maxBufferedMoveTime = 6 * printMoveBufferWait;
	recomputeParameters();
	linesCount = 0;
	linesTicksCount = 0;
	stop = false;
}

bool PathPlanner::queueSyncEvent(bool isBlocking /* = true */){
	PyThreadState *_save; 
	_save = PyEval_SaveThread();

	// If the move command buffer isn't empty, make the last line a sync event
	{	
		std::unique_lock<std::mutex> lk(line_mutex);
		if(linesCount > 0){
			unsigned int lastLine = (linesWritePos == 0) ? moveCacheSize - 1 : linesWritePos - 1;
			Path *p = &lines[lastLine];
			p->setSyncEvent(isBlocking);
			PyEval_RestoreThread(_save);
			return true;
		}
	}

	PyEval_RestoreThread(_save);
	return false;	// If the move command buffer is completly empty, it's too late.
}

// Wait for a sync event on the stepper PRU
int PathPlanner::waitUntilSyncEvent(){
    int ret;
	PyThreadState *_save; 
	_save = PyEval_SaveThread();
	ret = pru.waitUntilSync();
	PyEval_RestoreThread(_save);
    return ret;
}
                     
// Clear the sync event on the stepper PRU and resume operation.
void PathPlanner::clearSyncEvent(){
	PyThreadState *_save; 
	_save = PyEval_SaveThread();
	pru.resume();
	PyEval_RestoreThread(_save);
}

void PathPlanner::queueBatchMove(FLOAT_T* batchData, int batchSize, FLOAT_T speed, FLOAT_T accel, bool cancelable, bool optimize /* = true */) {
    FLOAT_T axis_diff[NUM_AXES];        // Axis movement in m
	PyThreadState *_save; 
	_save = PyEval_SaveThread();
    int numSegments = batchSize / (2 * NUM_AXES);

	unsigned int linesQueued = 0;
	unsigned int linesCacheRemaining = 0;
    long linesTicksRemaining = 0;
    long linesTicksQueued = 0;

	// Process each segment
	for(int segment_index = 0; segment_index < numSegments; segment_index++){
		// wait for the worker
		if(linesCacheRemaining == 0 || linesTicksRemaining == 0){
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
		if(stop){
		    PyEval_RestoreThread(_save);
			LOG( "Stopped/aborted/Cancelled while waiting for free move command space. linesCount: " << linesCount << std::endl);
		    return;
		}

		Path *p = &lines[linesWritePos];
        // Batch is packed into memory as a continious array.
		// SSSSEEEESSSSEEEESSSSEEEESSSSEEEE
		// ^0      ^8      ^16     ^24 (x sizeof(FLOAT_T))
		memcpy(p->startPos, /* startPos */ &batchData[segment_index * 2 * NUM_AXES], sizeof(FLOAT_T)*NUM_AXES);
		memcpy(p->endPos, /* endPos */ &batchData[segment_index * 2 * NUM_AXES + NUM_AXES], sizeof(FLOAT_T)*NUM_AXES);
        
		p->speed = speed; // Speed is in m/s
		p->accel = accel; // Accel is in m/s²
		p->joinFlags = 0;
		p->flags = 0;
		p->setCancelable(cancelable);
		p->setWaitMS(optimize ? printMoveBufferWait : 0);
		p->dir = 0;		

		//Find direction
		for(int axis=0; axis < NUM_AXES; axis++){
			p->startPos[axis] = ceil(p->startPos[axis]*axisStepsPerM[axis]);
			p->endPos[axis] = ceil(p->endPos[axis]*axisStepsPerM[axis]);
			p->delta[axis] = p->endPos[axis] - p->startPos[axis];

		    if(p->delta[axis]>=0)
				p->setPositiveDirectionForAxis(axis);
			else               
				p->delta[axis] = -p->delta[axis];
			axis_diff[axis] = p->delta[axis] / axisStepsPerM[axis];
			if(p->delta[axis]){ 
				p->setMoveOfAxis(axis);
                LOG( "Axis "<< axis << " is move since p->delta is " << p->delta[axis] << std::endl);
            }			
            LOG( "Axis "<< axis << " length is " << axis_diff[axis] << std::endl);
		}
		
		if(p->isNoMove()){
			LOG( "Warning: no move path" << std::endl);
			continue; // No steps included
		}

		//Define variables that are needed for the Bresenham algorithm.
        // Find the primary axis            
        p->primaryAxis = X_AXIS;
        float sum = 0;
        for(int i=0; i<NUM_AXES; i++){
            if(p->delta[i] > p->delta[p->primaryAxis])
                p->primaryAxis = i;
            sum += axis_diff[i] * axis_diff[i];
        }

		//LOG( "Primary axis is " << p->primaryAxis << std::endl);
		p->stepsRemaining = p->delta[p->primaryAxis];	    
        p->distance = sqrt(sum);

        //LOG("Distance in m:     " << p->distance << std::endl);
        //LOG("Speed in m/s:      " << p->speed << std::endl);
        //LOG("Accel in m/s²:     " << p->accel << std::endl);
        //LOG("StartSpeed in m/s: " << p->startSpeed << std::endl);
        //LOG("EndSpeed in m/s:   " << p->endSpeed << std::endl);

		calculateMove(p, axis_diff);
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
            linesTicksRemaining <= 0){
			{
                std::lock_guard<std::mutex> lk(line_mutex);
                linesCount += linesQueued;
                linesTicksCount += linesTicksQueued;
			}
			linesQueued = 0;
            linesTicksQueued = 0;
			lineAvailable.notify_all();
		}
		//LOG( "Line finished (" << linesQueued << " lines ready)." << std::endl);
	}
	//LOG( "End batch queuing move command" << std::endl);
	PyEval_RestoreThread(_save);
}

void PathPlanner::queueMove(FLOAT_T startPos[NUM_AXES],FLOAT_T endPos[NUM_AXES], FLOAT_T speed, FLOAT_T accel, bool cancelable, bool optimize) {
	FLOAT_T temp[NUM_AXES * 2];
	memcpy(temp, startPos, sizeof(FLOAT_T)*NUM_AXES);
	memcpy(&temp[NUM_AXES], endPos, sizeof(FLOAT_T)*NUM_AXES);	
	queueBatchMove( temp, NUM_AXES*2, speed, accel, cancelable, optimize);
}

FLOAT_T PathPlanner::safeSpeed(Path* p){
    FLOAT_T safe = 1e15;
    
    // Cap the speed based on axis. 
    // TODO: Add factor?
    for(int i=0; i<NUM_AXES; i++){
        if(p->isAxisMove(i)){
            safe = std::min(safe, minSpeeds[i]);
        }
    }
    safe = std::min(safe, p->fullSpeed);
    return safe;
}

void PathPlanner::calculateMove(Path* p, FLOAT_T axis_diff[NUM_AXES]){
    unsigned int axisInterval[NUM_AXES];
    float timeForMove = p->distance/p->speed;
    p->timeInTicks = timeForMove*F_CPU;
	
    //LOG( "CalucluateMove: Time for move is: " << timeForMove << " s" << std::endl);
    //LOG( "CalucluateMove: Time in ticks:    " << p->timeInTicks << " ticks" << std::endl);

    // Compute the slowest allowed interval (ticks/step), so maximum feedrate is not violated
    unsigned int limitInterval = (float)p->timeInTicks/(float)p->stepsRemaining; // until not violated by other constraints it is your target speed
    //LOG( "CalucluateMove: StepsRemaining " << p->stepsRemaining << " steps" << std::endl);
    //LOG( "CalucluateMove: limitInterval is " << limitInterval << " steps/s" << std::endl);
        
    for(int i=0; i<NUM_AXES; i++){
        if(p->isAxisMove(i)){
            axisInterval[i] = fabs(axis_diff[i] * F_CPU) / (maxSpeeds[i] * p->stepsRemaining); // m*ticks/s/(mm/s*steps) = ticks/step
            limitInterval = std::max(axisInterval[i], limitInterval);
        }
        else 
            axisInterval[i] = 0;
        //LOG( "CalucluateMove: AxisInterval " << i << ": " << axisInterval[i] << std::endl);
        //LOG( "CalucluateMove: AxisAccel   " << i << ": " << maxAccelerationMMPerSquareSecond[i] << std::endl);
    }
    //LOG( "CalucluateMove: limitInterval is " << limitInterval << " steps/s" << std::endl);
    p->fullInterval = limitInterval; // This is our target speed
	
    // new time at full speed = limitInterval*p->stepsRemaining [ticks]
    timeForMove = (limitInterval * p->stepsRemaining); 
    for(int i=0; i<NUM_AXES; i++){
        if(p->isAxisMove(i)){
            axisInterval[i] = timeForMove / p->delta[i];
            p->speeds[i] = -std::fabs(axis_diff[i] / timeForMove);
            if(p->isAxisNegativeMove(i))
                p->speeds[i] *= -1;
            //p->accels[i] = maxAccelerationMPerSquareSecond[i];
        }
        else 
            p->speeds[i] = 0;
    }

    p->fullSpeed = (p->distance / timeForMove)*F_CPU;
	
    // slowest time to accelerate from v0 to limitInterval determines used acceleration
    // t = (v_end-v_start)/a
    FLOAT_T slowest_axis_plateau_time_repro = 1e15; // repro to reduce division Unit: 1/s
    FLOAT_T *accel = maxAccelerationStepsPerSquareSecond;
    for(int i=0; i < NUM_AXES ; i++){
        if(p->isAxisMove(i)){
            // v = a * t => t = v/a = F_CPU/(c*a) => 1/t = c*a/F_CPU
            slowest_axis_plateau_time_repro = std::min(slowest_axis_plateau_time_repro, (FLOAT_T)axisInterval[i] * accel[i]); //  steps/s^2 * step/tick  Ticks/s^2
        }
    }

    //LOG("slowest_axis_plateau_time_repro: "<<slowest_axis_plateau_time_repro<<std::endl);
    //LOG("axisInterval[p->primaryAxis]: " << axisInterval[p->primaryAxis] << std::endl);

    // Errors for delta move are initialized in timer (except extruder)
    p->error[0] = p->error[1] = p->error[2] = p->delta[p->primaryAxis] >> 1;
    p->invFullSpeed = 1.0/p->fullSpeed;
    p->accelerationPrim = slowest_axis_plateau_time_repro / axisInterval[p->primaryAxis]; // a = v/t = F_CPU/(c*t): Steps/s^2

    //Now we can calculate the new primary axis acceleration, so that the slowest axis max acceleration is not violated
    p->fAcceleration = 262144.0*p->accelerationPrim/F_CPU; // (2^18)
    //LOG("p->accelerationPrim: " << p->accelerationPrim << " steps/s²"<< std::endl);
    //LOG("p->fAcceleration: " << p->fAcceleration << std::endl);

    p->accelerationDistance2 = 2.0*p->distance*slowest_axis_plateau_time_repro*p->fullSpeed/F_CPU; // m^2/s^2
    p->startSpeed = p->endSpeed = p->minSpeed = safeSpeed(p);
    // Can accelerate to full speed within the line
    if (p->startSpeed * p->startSpeed + p->accelerationDistance2 >= p->fullSpeed * p->fullSpeed)
        p->setNominalMove();
	
    //LOG("fullInterval: " << p->fullInterval << " ticks" << std::endl);
    //LOG("fullSpeed: " << p->fullSpeed << " m/s" << std::endl);

    p->vMax = F_CPU / p->fullInterval; // maximum steps per second, we can reach   
    //LOG("vMax for path is : " << p->vMax << " steps/s "<< std::endl);	
}

/** Update parameter used by updateTrapezoids
 
 Computes the acceleration/decelleration steps and advanced parameter associated.
 */
void Path::updateStepsParameter(){
    if(areParameterUpToDate() || isWarmUp()) 
        return;

    //LOG( "Path::updateStepsParameter()"<<std::endl);
    FLOAT_T startFactor = startSpeed * invFullSpeed;
    FLOAT_T endFactor   = endSpeed   * invFullSpeed;
    vStart = vMax * startFactor; //starting speed
    vEnd   = vMax * endFactor;
    //LOG("vStart is " << vStart << " steps/s" <<std::endl);
    FLOAT_T vmax2 = vMax*vMax;    
    accelSteps = (((vmax2 - (vStart * vStart)) / (accelerationPrim * 2)) + 1); // Always add 1 for missing precision
    decelSteps = (((vmax2 - (vEnd   * vEnd  )) / (accelerationPrim * 2)) + 1);	

    //LOG("accelSteps before cap: " << accelSteps << " steps" <<std::endl);
    if(accelSteps+decelSteps >= stepsRemaining){   // can't reach limit speed
        unsigned int red = (accelSteps+decelSteps + 2 - stepsRemaining) >> 1;
        accelSteps = accelSteps-std::min(accelSteps,red);
        decelSteps = decelSteps-std::min(decelSteps,red);
    }
    //LOG("accelSteps: " << accelSteps << " steps" <<std::endl);

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
void PathPlanner::updateTrapezoids(){
	unsigned int first = linesWritePos;
    Path *firstLine;
    Path *act = &lines[linesWritePos];
    unsigned int maxfirst = linesPos; // first non fixed segment

    //LOG("UpdateTRapezoids:: "<<std::endl);
    
    // Search last fixed element
    while(first != maxfirst && !lines[first].isEndSpeedFixed()){
        //LOG("caling previousPlannerIndex"<<std::endl);
        previousPlannerIndex(first);
    }
    if(first != linesWritePos && lines[first].isEndSpeedFixed()){
        //LOG("caling nextPlannerIndex"<<std::endl);
        nextPlannerIndex(first);
    }
    if(first == linesWritePos){   // Nothing to plan
        //LOG("Nothing to plan"<<std::endl);
        act->block();
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
    unsigned int previousIndex = linesWritePos;
    previousPlannerIndex(previousIndex);
    Path *previous = &lines[previousIndex];

	//LOG("UpdateTRapezoids:: computeMAxJunctionSpeed"<<std::endl);


    computeMaxJunctionSpeed(previous,act); // Set maximum junction speed if we have a real move before
    if(previous->isAxisOnlyMove(E_AXIS) != act->isAxisOnlyMove(E_AXIS)){
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
    do{
        lines[first].updateStepsParameter();
        lines[first].unblock();  // Flying block to release next used segment as early as possible
        nextPlannerIndex(first);
        lines[first].block();
    }
    while(first!=linesWritePos);
    act->updateStepsParameter();
    act->unblock();

    //LOG("UpdateTRapezoids:: done"<<std::endl);
}

// TODO: Remove dependency on Extruder. 
void PathPlanner::computeMaxJunctionSpeed(Path *previous, Path *current){
    FLOAT_T d[NUM_AXES];
    FLOAT_T jerk = 0; 
    FLOAT_T factor = 1;
    
    LOG("Computing Max junction speed"<<std::endl);
    

    for(int i=0; i<NUM_AXES; i++){
        d[i] = std::fabs(current->speeds[i] - previous->speeds[i])*F_CPU;
        jerk += d[i]*d[i];
    }

    jerk = sqrt(jerk);
    if(jerk>maxJerks[0])
        factor = maxJerks[0] / jerk;

    previous->maxJunctionSpeed = std::min(previous->fullSpeed * factor, current->fullSpeed);
    LOG("Max junction speed = "<<previous->maxJunctionSpeed<<std::endl);
}

/**
 Compute the maximum speed from the last entered move.
 The backwards planner traverses the moves from last to first looking at deceleration. The RHS of the accelerate/decelerate ramp.
 
 start = last line inserted
 last = last element until we check
 */
void PathPlanner::backwardPlanner(unsigned int start, unsigned int last){
    Path *act = &lines[start],*previous;
    FLOAT_T lastJunctionSpeed = act->endSpeed; // Start always with safe speed
	
    // Last element is already fixed in start speed
    while(start != last){
        previousPlannerIndex(start);
        previous = &lines[start];
		
        // Avoid speed calcs if we know we can accelerate within the line
        // acceleration is acceleration*distance*2! What can be reached if we try?
        lastJunctionSpeed = (act->isNominalMove() ? act->fullSpeed : sqrt(lastJunctionSpeed * lastJunctionSpeed + act->accelerationDistance2));
        // If that speed is more that the maximum junction speed allowed then ...
        if(lastJunctionSpeed >= previous->maxJunctionSpeed){   // Limit is reached
            // If the previous line's end speed has not been updated to maximum speed then do it now
            if(previous->endSpeed != previous->maxJunctionSpeed){
                previous->invalidateParameter(); // Needs recomputation
                previous->endSpeed = std::max(previous->minSpeed,previous->maxJunctionSpeed); // possibly unneeded???
            }
            // If actual line start speed has not been updated to maximum speed then do it now
            if(act->startSpeed != previous->maxJunctionSpeed){
                act->startSpeed = std::max(act->minSpeed,previous->maxJunctionSpeed); // possibly unneeded???
                act->invalidateParameter();
            }
            lastJunctionSpeed = previous->endSpeed;
        }
        else{
            // Block prev end and act start as calculated speed and recalculate plateau speeds (which could move the speed higher again)
            act->startSpeed = std::max(act->minSpeed,lastJunctionSpeed);
            lastJunctionSpeed = previous->endSpeed = std::max(lastJunctionSpeed,previous->minSpeed);
            previous->invalidateParameter();
            act->invalidateParameter();
        }
        act = previous;
    } // while loop
}

void PathPlanner::forwardPlanner(unsigned int first){
    Path *act;
    Path *next = &lines[first];
    FLOAT_T vmaxRight;
    FLOAT_T leftSpeed = next->startSpeed;
    while(first != linesWritePos){   // All except last segment, which has fixed end speed
        act = next;
        nextPlannerIndex(first);
        next = &lines[first];
		
        // Avoid speed calcs if we know we can accelerate within the line.
        vmaxRight = (act->isNominalMove() ? act->fullSpeed : sqrt(leftSpeed * leftSpeed + act->accelerationDistance2));
        if(vmaxRight > act->endSpeed){   // Could be higher next run?
            if(leftSpeed < act->minSpeed){
                leftSpeed = act->minSpeed;
                act->endSpeed = sqrt(leftSpeed * leftSpeed + act->accelerationDistance2);
            }
            act->startSpeed = leftSpeed;
            next->startSpeed = leftSpeed = std::max(std::min(act->endSpeed,act->maxJunctionSpeed),next->minSpeed);
            if(act->endSpeed == act->maxJunctionSpeed){  // Full speed reached, don't compute again!            
                act->setEndSpeedFixed(true);
                next->setStartSpeedFixed(true);
            }
            act->invalidateParameter();
        }
        else{     // We can accelerate full speed without reaching limit, which is as fast as possible. Fix it!
            act->fixStartAndEndSpeed();
            act->invalidateParameter();
            if(act->minSpeed > leftSpeed){
                leftSpeed = act->minSpeed;
                vmaxRight = sqrt(leftSpeed * leftSpeed + act->accelerationDistance2);
            }
            act->startSpeed = leftSpeed;
            act->endSpeed = std::max(act->minSpeed,vmaxRight);
            next->startSpeed = leftSpeed = std::max(std::min(act->endSpeed,act->maxJunctionSpeed),next->minSpeed);
            next->setStartSpeedFixed(true);
        }
    }
    next->startSpeed = std::max(next->minSpeed, leftSpeed); // This is the new segment, which is updated anyway, no extra flag needed.
}

void PathPlanner::runThread() {
	stop=false;
	pru.runThread();	
	runningThread = std::thread([this]() {
		this->run();
	});
}

void PathPlanner::stopThread(bool join) {
    Py_BEGIN_ALLOW_THREADS
	pru.stopThread(join);	
	stop=true;
	lineAvailable.notify_all();
	if(join && runningThread.joinable()) {
		runningThread.join();
	}
    Py_END_ALLOW_THREADS
}

PathPlanner::~PathPlanner() {
	if(runningThread.joinable()) {
		stopThread(true);
	}
}

void PathPlanner::waitUntilFinished() {
    Py_BEGIN_ALLOW_THREADS    
	std::unique_lock<std::mutex> lk(line_mutex);
	lineAvailable.wait(lk, [this]{
        return linesCount==0 || stop;
    });
	
	//Wait for PruTimer then
	if(!stop) {
		pru.waitUntilFinished();
	}
    Py_END_ALLOW_THREADS
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
		
		// If the buffer is half or more empty and the line to print is an optimized one, 
        // wait for 500 ms again so that we can get some other path in the path planner buffer, 
        // and we do that until the buffer is not anymore half empty.
		if(!isLinesBufferFilled() && cur->getWaitMS()>0 && waitUntilFilledUp) {
			unsigned lastCount = 0;
			LOG("Waiting for buffer to fill up. " << linesCount  << " lines pending, lastCount is " << lastCount << std::endl);
			do {
				lastCount = linesCount;				
				lineAvailable.wait_for(lk,  std::chrono::milliseconds(printMoveBufferWait), [this,lastCount]{
                    return linesCount>lastCount || stop;
                });				
			} while(lastCount<linesCount && linesCount<moveCacheSize && !stop);
			LOG("Done waiting for buffer to fill up... " << linesCount  << " lines ready. " << lastCount << std::endl);			
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
		
		long cur_errupd = 0;
		int directionMask = 0;      //0bCBAHEZYX
		int cancellableMask = 0;
		unsigned int vMaxReached;
        unsigned int timer_accel = 0;
		unsigned int timer_decel = 0;
	    unsigned int interval;
		
		if(cur->isBlocked()){   // This step is in computation - shouldn't happen
			cur = NULL;
			LOG( "Path planner thread: path " <<  std::dec << linesPos<< " is blocked, waiting... " << std::endl);
			std::this_thread::sleep_for( std::chrono::milliseconds(100) );
			continue;
		}
		
		// Only enable axes that are moving. If the axis doesn't need to move then it can stay disabled depending on configuration.
		cur->fixStartAndEndSpeed();
		cur_errupd = cur->delta[cur->primaryAxis];
		if(!cur->areParameterUpToDate()){  // should never happen, but with bad timings???
            LOG( "Path planner thread: Need to update paramters! This should not happen!" << std::endl);
			cur->updateStepsParameter();
		}
		
		vMaxReached = cur->vStart;
        // reset commands buffer every time
        cur->commands.clear();
        cur->commands.resize(cur->stepsRemaining);

        directionMask = 0;
        cancellableMask = 0;
        for(int i=0; i<NUM_AXES; i++){
            //LOG("Direction for axis " << i << " is " << cur->isAxisPositiveMove(i) << std::endl);
            directionMask |= (cur->isAxisPositiveMove(i) << i);
        }
		if(cur->isCancelable()) {
            for(int i=0; i<NUM_AXES; i++)
    			cancellableMask |= (cur->isAxisMove(i) << i);
		}		
        LOG("Direction mask: " << directionMask << std::endl);
        LOG("Cancel    mask: " << cancellableMask << std::endl);
		assert(cur);
		assert(cur->commands);


        LOG("startSpeed:   " << cur->startSpeed << std::endl);
        LOG("fullSpeed:    " << cur->fullSpeed << std::endl);
        LOG("acceleration: " << cur->accel << std::endl);
        LOG("accelTime:    " << ((cur->fullSpeed - cur->startSpeed)/cur->accel) << std::endl);
        
        

		for(unsigned int stepNumber=0; stepNumber<cur->stepsRemaining; stepNumber++){
			SteppersCommand& cmd = cur->commands.at(stepNumber);
			cmd.direction = (uint8_t) directionMask;
			cmd.cancellableMask = (uint8_t) cancellableMask;
			
			if((stepNumber == cur->stepsRemaining - 1) && cur->isSyncEvent()){
				if(cur->isSyncWaitEvent())
					cmd.options = STEPPER_COMMAND_OPTION_SYNCWAIT_EVENT;
				else
					cmd.options = STEPPER_COMMAND_OPTION_SYNC_EVENT;
			}
			else 
				cmd.options = 0;

            //LOG( "Doing step " << stepNumber << " of "<<cur->stepsRemaining <<std::endl);

			cmd.step = 0;
            for(int i=0; i<NUM_AXES; i++){
			    if(cur->isAxisMove(i)){
				    if((cur->error[i] -= cur->delta[i]) < 0){
					    cmd.step |= (1 << i);
					    cur->error[i] += cur_errupd;
				    }
			    }
            }

			//If acceleration is enabled on this move and we are in the acceleration segment, calculate the current interval
			if (cur->moveAccelerating(stepNumber)){   // we are accelerating
                //LOG( "Acceleration" << std::endl);
                vMaxReached = ComputeV(timer_accel, cur->fAcceleration) + cur->vStart;
				if(vMaxReached>cur->vMax) 
                    vMaxReached = cur->vMax;
				unsigned long v = vMaxReached;
				interval = F_CPU/(v);
				timer_accel+=interval;
			}
			else if (cur->moveDecelerating(stepNumber)){     // time to slow down
				//LOG( "Decelleration "<<std::endl);
				unsigned long v = ComputeV(timer_decel, cur->fAcceleration);
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
			else{ // full speed reached
                //LOG( "Cruising "<<std::endl);
				interval = cur->fullInterval;
			}

    		//LOG("Interval: " << interval << std::endl);
			assert(interval < F_CPU*4);
			cmd.delay = (uint32_t)interval;
		} // stepsRemaining
		

		//LOG("Current move time " << pru.getTotalQueuedMovesTime() / (double) F_CPU << std::endl);
		
		//Wait until we need to push some lines so that the path planner can fill up
		pru.waitUntilLowMoveTime((F_CPU/1000)*minBufferedMoveTime); //in seconds
		
		LOG( "Sending " << std::dec << linesPos << ", Start speed=" << cur->startSpeed << ", end speed="<<cur->endSpeed << ", nb steps = " << cur->stepsRemaining << std::endl);
		
		pru.push_block((uint8_t*)cur->commands.data(), sizeof(SteppersCommand)*cur->stepsRemaining, sizeof(SteppersCommand), linesPos, cur->timeInTicks);
		//LOG( "Done sending with " << std::dec << linesPos << std::endl);
		
		removeCurrentLine();
		lineAvailable.notify_all();
	}
}
