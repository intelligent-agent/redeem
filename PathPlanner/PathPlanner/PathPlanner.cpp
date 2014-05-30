//
//  PathPlanner.cpp
//  PathPlanner
//
//  Created by Mathieu on 29.05.14.
//  Copyright (c) 2014 Xwaves. All rights reserved.
//

#include "PathPlanner.h"
#include <cmath>
#include <assert.h>
#include <thread>

#define F_CPU 200000000


void PathPlanner::setMaxFeedrates(unsigned long rates[NUM_AXIS]){
	memcpy(maxFeedrate, rates, sizeof(unsigned long)*NUM_AXIS);
}

void PathPlanner::setPrintAcceleration(unsigned long accel[NUM_AXIS]){
	memcpy(maxAccelerationMMPerSquareSecond, accel, sizeof(unsigned long)*NUM_AXIS);
	recomputeParameters();
}

void PathPlanner::setTravelAcceleration(unsigned long accel[NUM_AXIS]){
	memcpy(maxTravelAccelerationMMPerSquareSecond, accel, sizeof(unsigned long)*NUM_AXIS);
	recomputeParameters();
}

void PathPlanner::setMaxJerk(unsigned long maxJerk, unsigned long maxZJerk){
	this->maxJerk = maxJerk;
	this->maxZJerk = maxZJerk;
}

void PathPlanner::setMaximumExtruderStartFeedrate(unsigned long maxstartfeedrate) {
	this->Extruder_maxStartFeedrate = maxstartfeedrate;
}

void PathPlanner::setAxisStepsPerMM(unsigned long stepPerMM[NUM_AXIS]) {
	memcpy(axisStepsPerMM, stepPerMM, sizeof(unsigned long)*NUM_AXIS);
	recomputeParameters();
}

void PathPlanner::recomputeParameters() {
	for(uint8_t i=0; i<NUM_AXIS; i++)
    {
		invAxisStepsPerMM[i]=1.0/axisStepsPerMM[i];
        /** Acceleration in steps/s^3 in printing mode.*/
        maxPrintAccelerationStepsPerSquareSecond[i] =  maxAccelerationMMPerSquareSecond[i] * (axisStepsPerMM[i]);
        /** Acceleration in steps/s^2 in movement mode.*/
        maxTravelAccelerationStepsPerSquareSecond[i] = maxTravelAccelerationMMPerSquareSecond[i] * (axisStepsPerMM[i]);
    }
	
	
	float accel = std::max(maxAccelerationMMPerSquareSecond[X_AXIS],maxTravelAccelerationMMPerSquareSecond[X_AXIS]);
    minimumSpeed = accel*sqrt(2.0f/(axisStepsPerMM[X_AXIS]*accel));
    accel = std::max(maxAccelerationMMPerSquareSecond[Z_AXIS],maxTravelAccelerationMMPerSquareSecond[Z_AXIS]);
    minimumZSpeed = accel*sqrt(2.0f/(axisStepsPerMM[Z_AXIS]*accel));

}

PathPlanner::PathPlanner() {
	linesPos = 0;
	linesWritePos = 0;
	
	maxFeedrate[0]=200;
	maxFeedrate[1]=200;
	maxFeedrate[2]=5;
	maxFeedrate[3]=200;
	//maxFeedrate[4]=200;
	
	axisStepsPerMM[0]=50;
	axisStepsPerMM[1]=50;
	axisStepsPerMM[2]=2133.33333;
	axisStepsPerMM[3]=535;
	//axisStepsPerMM[4]=535;
	
	maxAccelerationMMPerSquareSecond[0]=1000;
	maxAccelerationMMPerSquareSecond[1]=1000;
	maxAccelerationMMPerSquareSecond[2]=100;
	maxAccelerationMMPerSquareSecond[3]=1000;
	//maxAccelerationMMPerSquareSecond[4]=1000;
	
	maxTravelAccelerationMMPerSquareSecond[0]=2000;
	maxTravelAccelerationMMPerSquareSecond[1]=2000;
	maxTravelAccelerationMMPerSquareSecond[2]=200;
	maxTravelAccelerationMMPerSquareSecond[3]=2000;
	//maxTravelAccelerationMMPerSquareSecond[4]=2000;
	
		
	Extruder_maxStartFeedrate=10;
	maxJerk =20;
	maxZJerk= 0.3;
	recomputeParameters();
	
	linesCount = 0;
	
	stop = false;
	bzero(lines, sizeof(lines));
}

void PathPlanner::queueMove(float startPos[NUM_AXIS],float endPos[NUM_AXIS],float speed) {
    float axis_diff[NUM_AXIS]; // Axis movement in mm
	
	// wait for the worker
    if(linesCount>=MOVE_CACHE_SIZE){
        std::unique_lock<std::mutex> lk(m);
        lineAvailable.wait(lk, [this]{return linesCount<MOVE_CACHE_SIZE;});
    }
	
	Path *p = &lines[linesWritePos];
	
	if(p->commands) {
		delete[] p->commands;
		p->commands=NULL;
	}
	
	memcpy(p->startPos, startPos, sizeof(float)*NUM_AXIS);
	memcpy(p->endPos, endPos, sizeof(float)*NUM_AXIS);
	
	logger << std::dec << "Moving from " << startPos[0] << "," << startPos[1] << "," << startPos[2] << " to "
	 << endPos[0] << "," << endPos[1] << "," << endPos[2] << std::endl;
	
	p->speed = speed;
	
    p->joinFlags = 0;
	p->commands=NULL;
	
    p->dir = 0;
    //Printer::constrainDestinationCoords();
	
    //Find direction
    for(uint8_t axis=0; axis < NUM_AXIS; axis++)
    {
        if((p->delta[axis]=p->endPos[axis]-p->startPos[axis])>=0)
            p->setPositiveDirectionForAxis(axis);
        else
            p->delta[axis] = -p->delta[axis];
		
        axis_diff[axis] = p->delta[axis] * invAxisStepsPerMM[axis];
        if(p->delta[axis]) p->setMoveOfAxis(axis);
		
    }
	
    if(p->isNoMove())
	{
		std::cout << "Warning: no move path" << std::endl;
		// if(newPath)   // need to delete dummy elements, otherwise commands can get locked.
		// resetPathPlanner();
		return; // No steps included
	}
	
	
    float xydist2;
	
	
    //Define variables that are needed for the Bresenham algorithm. Please note that  Z is not currently included in the Bresenham algorithm.
    if(p->delta[Y_AXIS] > p->delta[X_AXIS] && p->delta[Y_AXIS] > p->delta[Z_AXIS] && p->delta[Y_AXIS] > p->delta[E_AXIS]) p->primaryAxis = Y_AXIS;
    else if (p->delta[X_AXIS] > p->delta[Z_AXIS] && p->delta[X_AXIS] > p->delta[E_AXIS]) p->primaryAxis = X_AXIS;
    else if (p->delta[Z_AXIS] > p->delta[E_AXIS]) p->primaryAxis = Z_AXIS;
    else p->primaryAxis = E_AXIS;
    p->stepsRemaining = p->delta[p->primaryAxis];
    
	if(p->isXYZMove())
    {
        xydist2 = axis_diff[X_AXIS] * axis_diff[X_AXIS] + axis_diff[Y_AXIS] * axis_diff[Y_AXIS];
        if(p->isZMove())
            p->distance = std::max((float)sqrt(xydist2 + axis_diff[Z_AXIS] * axis_diff[Z_AXIS]),(float)fabs(axis_diff[E_AXIS]));
        else
            p->distance = std::max((float)sqrt(xydist2),(float)fabs(axis_diff[E_AXIS]));
    }
    else
        p->distance = fabs(axis_diff[E_AXIS]);
	
    calculateMove(p,axis_diff);
	
	linesWritePos++;
	if(linesWritePos>=MOVE_CACHE_SIZE) linesWritePos = 0;
	
	// BEGIN_INTERRUPT_PROTECTED
	
	// send data to the worker thread
    {
        std::lock_guard<std::mutex> lk(m);
        linesCount++;
    }
    lineAvailable.notify_all();
	
	// END_INTERRUPT_PROTECTED
}

float PathPlanner::safeSpeed(Path* p)
{
    float safe = maxJerk * 0.5;
	
    if(p->isZMove())
    {
        if(p->primaryAxis == Z_AXIS)
        {
            safe = maxZJerk*0.5*p->fullSpeed/fabs(p->speedZ);
        }
        else if(fabs(p->speedZ) > maxZJerk * 0.5)
            safe = std::min(safe,(float)(maxZJerk * 0.5 * p->fullSpeed / fabs(p->speedZ)));
    }
	
    if(p->isEMove())
    {
        if(p->isXYZMove())
            safe = std::min(safe,(float)(0.5*Extruder_maxStartFeedrate*p->fullSpeed/fabs(p->speedE)));
        else
            safe = 0.5*Extruder_maxStartFeedrate; // This is a retraction move
    }
    if(p->primaryAxis == X_AXIS || p->primaryAxis == Y_AXIS) // enforce minimum speed for numerical stability of explicit speed integration
        safe = std::max(minimumSpeed,safe);
    else if(p->primaryAxis == Z_AXIS)
    {
        safe = std::max(minimumZSpeed,safe);
    }
    return std::min(safe,p->fullSpeed);
}

void PathPlanner::calculateMove(Path* p,float axis_diff[NUM_AXIS])
{
    unsigned int axisInterval[NUM_AXIS];
    float timeForMove = (float)(F_CPU)*p->distance / p->speed; // time is in ticks
	// bool critical = false;
	/* if(linesCount < MOVE_CACHE_LOW && timeForMove < LOW_TICKS_PER_MOVE)   // Limit speed to keep cache full.
	 {
	 //OUT_P_I("L:",lines_count);
	 timeForMove += (3 * (LOW_TICKS_PER_MOVE-timeForMove)) / (linesCount+1); // Increase time if queue gets empty. Add more time if queue gets smaller.
	 //OUT_P_F_LN("Slow ",time_for_move);
	 critical=true;
	 }*/
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
        axisInterval[Z_AXIS] = fabs((float)axis_diff[Z_AXIS])*(float)F_CPU/(float)(maxFeedrate[Z_AXIS]*p->stepsRemaining); // must prevent overflow!
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
    timeForMove = (float)limitInterval * (float)p->stepsRemaining; // for large z-distance this overflows with long computation
    float inv_time_s = (float)F_CPU / timeForMove;
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
    float slowest_axis_plateau_time_repro = 1e15; // repro to reduce division Unit: 1/s
    unsigned long *accel = (p->isEPositiveMove() ?  maxPrintAccelerationStepsPerSquareSecond : maxTravelAccelerationStepsPerSquareSecond);
    for(uint8_t i=0; i < 4 ; i++)
    {
        if(p->isMoveOfAxis(i))
            // v = a * t => t = v/a = F_CPU/(c*a) => 1/t = c*a/F_CPU
            slowest_axis_plateau_time_repro = std::min(slowest_axis_plateau_time_repro,(float)axisInterval[i] * (float)accel[i]); //  steps/s^2 * step/tick  Ticks/s^2
    }
    // Errors for delta move are initialized in timer (except extruder)
    p->error[0] = p->error[1] = p->error[2] = p->delta[p->primaryAxis] >> 1;
    p->invFullSpeed = 1.0/p->fullSpeed;
    p->accelerationPrim = slowest_axis_plateau_time_repro / axisInterval[p->primaryAxis]; // a = v/t = F_CPU/(c*t): Steps/s^2
    //Now we can calculate the new primary axis acceleration, so that the slowest axis max acceleration is not violated
    p->fAcceleration = 262144.0*(float)p->accelerationPrim/F_CPU; // will overflow without float!
    p->accelerationDistance2 = 2.0*p->distance*slowest_axis_plateau_time_repro*p->fullSpeed/((float)F_CPU); // mm^2/s^2
    p->startSpeed = p->endSpeed = p->minSpeed = safeSpeed(p);
    // Can accelerate to full speed within the line
    if (p->startSpeed * p->startSpeed + p->accelerationDistance2 >= p->fullSpeed * p->fullSpeed)
        p->setNominalMove();
	
    p->vMax = F_CPU / p->fullInterval; // maximum steps per second, we can reach
    // if(p->vMax>46000)  // gets overflow in N computation
    //   p->vMax = 46000;
    //p->plateauN = (p->vMax*p->vMax/p->accelerationPrim)>>1;
	
    updateTrapezoids();
    // how much steps on primary axis do we need to reach target feedrate
    //p->plateauSteps = (long) (((float)p->acceleration *0.5f / slowest_axis_plateau_time_repro + p->vMin) *1.01f/slowest_axis_plateau_time_repro);
	
}

/** Update parameter used by updateTrapezoids
 
 Computes the acceleration/decelleration steps and advanced parameter associated.
 */
void Path::updateStepsParameter()
{
    if(areParameterUpToDate() || isWarmUp()) return;
    float startFactor = startSpeed * invFullSpeed;
    float endFactor   = endSpeed   * invFullSpeed;
    vStart = vMax * startFactor; //starting speed
    vEnd   = vMax * endFactor;
    uint64_t vmax2 = static_cast<uint64_t>(vMax) * static_cast<uint64_t>(vMax);
    accelSteps = ((vmax2 - static_cast<uint64_t>(vStart) * static_cast<uint64_t>(vStart)) / (accelerationPrim<<1)) + 1; // Always add 1 for missing precision
    decelSteps = ((vmax2 - static_cast<uint64_t>(vEnd) * static_cast<uint64_t>(vEnd))  /(accelerationPrim<<1)) + 1;
	
	
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
    if(maxfirst != linesWritePos)
        nextPlannerIndex(maxfirst); // don't touch the line printing
    // Now ignore enough segments to gain enough time for path planning
    int32_t timeleft = 0;
    // Skip as many stored moves as needed to gain enough time for computation
    long long minTime = 4500L * std::min(MOVE_CACHE_SIZE,10);
    while(timeleft < minTime && maxfirst != linesWritePos)
    {
        timeleft += lines[maxfirst].timeInTicks;
        nextPlannerIndex(maxfirst);
    }
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
    if((previous->primaryAxis == Z_AXIS && act->primaryAxis != Z_AXIS) || (previous->primaryAxis != Z_AXIS && act->primaryAxis == Z_AXIS))
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
    float dx = current->speedX-previous->speedX;
    float dy = current->speedY-previous->speedY;
    float factor = 1;
    float jerk = sqrt(dx*dx + dy*dy);
    if(jerk>maxJerk)
        factor = maxJerk / jerk;
	
    if((previous->dir | current->dir) & 64)
    {
        float dz = fabs(current->speedZ - previous->speedZ);
        if(dz>maxZJerk)
            factor = std::min(factor,maxZJerk / dz);
    }
	
    float eJerk = fabs(current->speedE - previous->speedE);
    if(eJerk > Extruder_maxStartFeedrate)
        factor = std::min(factor,Extruder_maxStartFeedrate / eJerk);
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
    float lastJunctionSpeed = act->endSpeed; // Start always with safe speed
	
    //PREVIOUS_PLANNER_INDEX(last); // Last element is already fixed in start speed
    while(start != last)
    {
        previousPlannerIndex(start);
        previous = &lines[start];
		
		
        /* if(prev->isEndSpeedFixed())   // Nothing to update from here on, happens when path optimize disabled
         {
		 act->setStartSpeedFixed(true);
		 return;
         }*/
		
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
    float vmaxRight;
    float leftSpeed = next->startSpeed;
    while(first != linesWritePos)   // All except last segment, which has fixed end speed
    {
        act = next;
        nextPlannerIndex(first);
        next = &lines[first];
        /* if(act->isEndSpeedFixed())
         {
		 leftSpeed = act->endSpeed;
		 continue; // Nothing to do here
         }*/
		
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
	
	pru.stopThread(join);
	
	stop=true;
	lineAvailable.notify_all();
	if(join && runningThread.joinable()) {
		runningThread.join();
	}
	
	
}

PathPlanner::~PathPlanner() {
	for(unsigned i = 0;i<MOVE_CACHE_SIZE;i++) {
		if(lines[i].commands) {
			delete[] lines[i].commands;
			lines[i].commands=NULL;
		}
	}
	
	if(runningThread.joinable()) {
		stopThread(true);
	}
}

void PathPlanner::waitUntilFinished() {
	std::unique_lock<std::mutex> lk(m);
	lineAvailable.wait(lk, [this]{return linesCount==0 || stop;});
	
	//Wait for PruTimer then
	if(!stop) {
		pru.waitUntilFinished();
	}
}

void PathPlanner::run() {
	while(!stop) {
		
		std::unique_lock<std::mutex> lk(m);
		lineAvailable.wait(lk, [this]{return linesCount>0 || stop;});
		
		
		
		lk.unlock();

		
		if(!linesCount)
		{
			continue;
		}
		
		long cur_errupd=0;
		uint8_t directionMask = 0; //0b000HEZYX
		
		
		
		unsigned int vMaxReached ;
		unsigned int timer = 0;
		
		
		Path* cur = &lines[linesPos];
		if(cur->isBlocked())   // This step is in computation - shouldn't happen
		{
			/*if(lastblk!=(int)cur) // can cause output errors!
			 {
			 HAL::allowInterrupts();
			 lastblk = (int)cur;
			 Com::printFLN(Com::tBLK,lines_count);
			 }*/
			cur = NULL;
			//return 2000;
			std::this_thread::sleep_for( std::chrono::milliseconds(100) );
			continue;
		}
		//HAL::allowInterrupts();
		//lastblk = -1;
		
		if(cur->isWarmUp())
		{
			// This is a warmup move to initalize the path planner correctly. Just waste
			// a bit of time to get the planning up to date.
			if(linesCount<=cur->getWaitForXLinesFilled())
			{
				cur = NULL;
				
				std::this_thread::sleep_for( std::chrono::milliseconds(100) );
				continue;
			}
			
#warning TODO
			/*long wait = cur->getWaitTicks();
			 
			 removeCurrentLineForbidInterrupt();
			 
			 return(wait); // waste some time for path optimization to fill up*/
			std::this_thread::sleep_for( std::chrono::milliseconds(100) );
			continue;
		} // End if WARMUP
		
		//Only enable axis that are moving. If the axis doesn't need to move then it can stay disabled depending on configuration.
		
		/*if(cur->isXMove()) Printer::enableXStepper();
		 if(cur->isYMove()) Printer::enableYStepper();
		 
		 if(cur->isZMove())
		 {
		 Printer::enableZStepper();
		 }
		 if(cur->isEMove()) Extruder::enable();*/
		
		cur->fixStartAndEndSpeed();
		
		//HAL::allowInterrupts();
		cur_errupd = cur->delta[cur->primaryAxis];
		if(!cur->areParameterUpToDate())  // should never happen, but with bad timings???
		{
			cur->updateStepsParameter();
		}
		
		
		vMaxReached = cur->vStart;
		
		
		
		
		//HAL::forbidInterrupts();
		//Determine direction of movement,check if endstop was hit
		if(cur->commands) {
			delete[] cur->commands;
		}
		cur->commands = new SteppersCommand[cur->stepsRemaining];
		
		
		
		directionMask|=((uint8_t)cur->isYPositiveMove() << X_AXIS);
		directionMask|=((uint8_t)cur->isYPositiveMove() << Y_AXIS);
		directionMask|=((uint8_t)cur->isZPositiveMove() << Z_AXIS);
		directionMask|=((uint8_t)cur->isEPositiveMove() << E_AXIS);
		
		
		/*if(Printer::wasLastHalfstepping && cur->isFullstepping())   // Switch halfstepping -> full stepping
		 {
		 Printer::wasLastHalfstepping = 0;
		 return Printer::interval+Printer::interval+Printer::interval; // Wait an other 150% from last half step to make the 100% full
		 }
		 else if(!Printer::wasLastHalfstepping && !cur->isFullstepping())     // Switch full to half stepping
		 {
		 Printer::wasLastHalfstepping = 1;
		 }
		 else
		 return Printer::interval; // Wait an other 50% from last step to make the 100% full*/
		
		
		
		assert(cur);
		assert(cur->commands);
		
		//HAL::allowInterrupts();
		/* For halfstepping, we divide the actions into even and odd actions to split
		 time used per loop. */
		//HAL::forbidInterrupts();
		//if(doEven) cur->checkEndstops();
		
		
		unsigned int interval=0;
		for(unsigned int stepNumber=0; stepNumber<cur->stepsRemaining; stepNumber++)
		{
			
			
			SteppersCommand& cmd = cur->commands[stepNumber];
			cmd.direction = directionMask;
			cmd.options = 0;
			cmd.step = 0;
			if(cur->isEMove())
			{
				if((cur->error[E_AXIS] -= cur->delta[E_AXIS]) < 0)
				{
					cmd.step |= (1 << E_AXIS);
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
			
			//Printer::insertStepperHighDelay();
			
			//Extruder::unstep();
			//Printer::endXYZSteps();
			//} // for loop
			
			
			
			
			//HAL::allowInterrupts(); // Allow interrupts for other types, timer1 is still disabled
			
#define ComputeV(timer,accel)  (((timer>>8)*accel)>>10)
			
			//If acceleration is enabled on this move and we are in the acceleration segment, calculate the current interval
			if (cur->moveAccelerating(stepNumber))   // we are accelerating
			{
				vMaxReached = ComputeV(timer,cur->fAcceleration)+cur->vStart;
				if(vMaxReached>cur->vMax) vMaxReached = cur->vMax;
				unsigned int v = vMaxReached;
				interval = F_CPU/(v);
				timer+=interval;
			}
			else if (cur->moveDecelerating(stepNumber))     // time to slow down
			{
				unsigned int v = ComputeV(timer,cur->fAcceleration);
				if (v > vMaxReached)   // if deceleration goes too far it can become too large
					v = cur->vEnd;
				else
				{
					v=vMaxReached - v;
					if (v<cur->vEnd) v = cur->vEnd; // extra steps at the end of desceleration due to rounding erros
				}
				
				interval = F_CPU/(v);
				timer += interval;
			}
			else // full speed reached
			{
				// constant speed reached
				interval = cur->fullInterval;
			}
			//std::cout << interval << std::endl;
			
			
			cmd.delay = interval;
		} // stepsRemaining
				
		logger << "Done with " << std::dec << linesPos << std::endl;
		
		logger << "Sending " << std::dec << linesPos << std::endl;
		
		pru.push_block((uint8_t*)cur->commands, sizeof(SteppersCommand)*cur->stepsRemaining, sizeof(SteppersCommand));
		
		logger << "Done sending with " << std::dec << linesPos << std::endl;
		
		
		removeCurrentLineForbidInterrupt();
		
		lineAvailable.notify_all();
	}
}
