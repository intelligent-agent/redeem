//
//  Path.cpp
//  PathPlanner
//
//  Created by Mathieu on 29.05.14.
//  Copyright (c) 2014 Xwaves. All rights reserved.
//

#include "Path.h"
#include <cmath>

/*
 This file is part of Repetier-Firmware.
 
 Repetier-Firmware is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.
 
 Repetier-Firmware is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
 along with Repetier-Firmware.  If not, see <http://www.gnu.org/licenses/>.
 
 This firmware is a nearly complete rewrite of the sprinter firmware
 by kliment (https://github.com/kliment/Sprinter)
 which based on Tonokip RepRap firmware rewrite based off of Hydra-mmm firmware.
 
 Functions in this file are used to communicate using ascii or repetier protocol.
 */

#define STEPPER_INACTIVE_TIME 360
/** After x seconds of inactivity, the system will go down as far it can.
 It will at least disable all stepper motors and heaters. If the board has
 a power pin, it will be disabled, too.
 Set value to 0 for disabled.
 Overridden if EEPROM activated.
 */
#define MAX_INACTIVE_TIME 0L
#define MOVE_CACHE_LOW 10
#define F_CPU       200000000
#define LOW_TICKS_PER_MOVE 250000
/** Set max. frequency to 150000Hz */
#define LIMIT_INTERVAL (F_CPU/150000)
/** The firmware supports trajectory smoothing. To achieve this, it divides the stepsize by 2, resulting in
 the double computation cost. For slow movements this is not an issue, but for really fast moves this is
 too much. The value specified here is the number of clock cycles between a step on the driving axis.
 If the interval at full speed is below this value, smoothing is disabled for that line.*/
#define MAX_HALFSTEP_INTERVAL 1999


class RMath {
public:
    static inline float min(float a,float b) {
        if(a<b) return a;
        return b;
    }
    static inline float max(float a,float b) {
        if(a<b) return b;
        return a;
    }
    static inline long min(long a,long b) {
        if(a<b) return a;
        return b;
    }
    static inline long max(long a,long b) {
        if(a<b) return b;
        return a;
    }
    static inline int min(int a,int b) {
        if(a<b) return a;
        return b;
    }
    static inline int max(int a,int b) {
        if(a<b) return b;
        return a;
    }
    static inline unsigned int min(unsigned int a,unsigned int b) {
        if(a<b) return a;
        return b;
    }
    static inline unsigned int max(unsigned int a,unsigned int b) {
        if(a<b) return b;
        return a;
    }
    static inline long sqr(long a) {return a*a;}
    static inline float sqr(float a) {return a*a;}
};


//Inactivity shutdown variables
millis_t previousMillisCmd = 0;
millis_t maxInactiveTime = MAX_INACTIVE_TIME*1000L;
millis_t stepperInactiveTime = STEPPER_INACTIVE_TIME*1000L;

volatile int waitRelax = 0; // Delay filament relax at the end of print, could be a simple timeout

PrintLine PrintLine::lines[MOVE_CACHE_SIZE]; ///< Cache for print moves.
PrintLine *PrintLine::cur = 0;               ///< Current printing line
#if CPU_ARCH==ARCH_ARM
volatile bool PrintLine::nlFlag = false;
#endif
uint8_t PrintLine::linesWritePos = 0;            ///< Position where we write the next cached line move.
volatile uint8_t PrintLine::linesCount = 0;      ///< Number of lines cached 0 = nothing to do.
uint8_t PrintLine::linesPos = 0;                 ///< Position for executing line movement.

/**
 Move printer the given number of steps. Puts the move into the queue. Used by e.g. homing commands.
 */
void PrintLine::moveRelativeDistanceInSteps(long x,long y,long z,long e,float feedrate,bool waitEnd,bool checkEndstop)
{
    //Com::printF(Com::tJerkColon,x);
    //Com::printF(Com::tComma,y);
    //Com::printFLN(Com::tComma,z);
    float savedFeedrate = Printer::feedrate;
    Printer::destinationSteps[X_AXIS] = Printer::currentPositionSteps[X_AXIS] + x;
    Printer::destinationSteps[Y_AXIS] = Printer::currentPositionSteps[Y_AXIS] + y;
    Printer::destinationSteps[Z_AXIS] = Printer::currentPositionSteps[Z_AXIS] + z;
    Printer::destinationSteps[E_AXIS] = Printer::currentPositionSteps[E_AXIS] + e;
    Printer::feedrate = feedrate;
    queueCartesianMove(checkEndstop,false);
    Printer::feedrate = savedFeedrate;
    Printer::updateCurrentPosition();
   /* if(waitEnd)
        Commands::waitUntilEndOfAllMoves();
    previousMillisCmd = HAL::timeInMilliseconds();*/
}

void PrintLine::moveRelativeDistanceInStepsReal(long x,long y,long z,long e,float feedrate,bool waitEnd)
{
    Printer::lastCmdPos[X_AXIS] += x * Printer::invAxisStepsPerMM[X_AXIS];
    Printer::lastCmdPos[Y_AXIS] += y * Printer::invAxisStepsPerMM[Y_AXIS];
    Printer::lastCmdPos[Z_AXIS] += z * Printer::invAxisStepsPerMM[Z_AXIS];
    if(!Printer::isPositionAllowed( Printer::lastCmdPos[X_AXIS], Printer::lastCmdPos[Y_AXIS], Printer::lastCmdPos[Z_AXIS]))
    {
        return; // ignore move
    }
    Printer::moveToReal(Printer::lastCmdPos[X_AXIS],Printer::lastCmdPos[Y_AXIS],Printer::lastCmdPos[Z_AXIS],
                        (Printer::currentPositionSteps[E_AXIS] + e) * Printer::invAxisStepsPerMM[E_AXIS],feedrate);
    Printer::updateCurrentPosition();
  /*  if(waitEnd)
        Commands::waitUntilEndOfAllMoves();
    previousMillisCmd = HAL::timeInMilliseconds();*/
}

/**
 Put a move to the current destination coordinates into the movement cache.
 If the cache is full, the method will wait, until a place gets free. During
 wait communication and temperature control is enabled.
 @param check_endstops Read endstop during move.
 */
void PrintLine::queueCartesianMove(uint8_t check_endstops,uint8_t pathOptimize)
{
    Printer::unsetAllSteppersDisabled();
    waitForXFreeLines(1);
    uint8_t newPath=insertWaitMovesIfNeeded(pathOptimize, 0);
    PrintLine *p = getNextWriteLine();
	
    float axis_diff[4]; // Axis movement in mm
    if(check_endstops) p->flags = FLAG_CHECK_ENDSTOPS;
    else p->flags = 0;
    p->joinFlags = 0;
    if(!pathOptimize) p->setEndSpeedFixed(true);
    p->dir = 0;
    Printer::constrainDestinationCoords();
    //Find direction
    for(uint8_t axis=0; axis < 4; axis++)
    {
        if((p->delta[axis]=Printer::destinationSteps[axis]-Printer::currentPositionSteps[axis])>=0)
            p->setPositiveDirectionForAxis(axis);
        else
            p->delta[axis] = -p->delta[axis];
        if(axis == E_AXIS && Printer::extrudeMultiply!=100)
            p->delta[E_AXIS] = (long)((p->delta[E_AXIS] * (float)Printer::extrudeMultiply) * 0.01f);
        axis_diff[axis] = p->delta[axis] * Printer::invAxisStepsPerMM[axis];
        if(p->delta[axis]) p->setMoveOfAxis(axis);
        Printer::currentPositionSteps[axis] = Printer::destinationSteps[axis];
    }
    if(p->isNoMove())
    {
        if(newPath)   // need to delete dummy elements, otherwise commands can get locked.
            resetPathPlanner();
        return; // No steps included
    }
    Printer::filamentPrinted += axis_diff[E_AXIS];
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
            p->distance = RMath::max((float)sqrt(xydist2 + axis_diff[Z_AXIS] * axis_diff[Z_AXIS]),fabs(axis_diff[E_AXIS]));
        else
            p->distance = RMath::max((float)sqrt(xydist2),fabs(axis_diff[E_AXIS]));
    }
    else
        p->distance = fabs(axis_diff[E_AXIS]);
    p->calculateMove(axis_diff,pathOptimize);
}


void PrintLine::calculateMove(float axis_diff[],uint8_t pathOptimize)
{
    long axisInterval[4];
    float timeForMove = (float)(F_CPU)*distance / (isXOrYMove() ? RMath::max(Printer::minimumSpeed,Printer::feedrate): Printer::feedrate); // time is in ticks
    bool critical = Printer::isZProbingActive();
    if(linesCount < MOVE_CACHE_LOW && timeForMove < LOW_TICKS_PER_MOVE)   // Limit speed to keep cache full.
    {
        //OUT_P_I("L:",lines_count);
        timeForMove += (3 * (LOW_TICKS_PER_MOVE-timeForMove)) / (linesCount+1); // Increase time if queue gets empty. Add more time if queue gets smaller.
        //OUT_P_F_LN("Slow ",time_for_move);
        critical=true;
    }
    timeInTicks = timeForMove;

    // Compute the solwest allowed interval (ticks/step), so maximum feedrate is not violated
    long limitInterval = timeForMove/stepsRemaining; // until not violated by other constraints it is your target speed
    if(isXMove())
    {
        axisInterval[X_AXIS] = fabs(axis_diff[X_AXIS]) * F_CPU / (Printer::maxFeedrate[X_AXIS] * stepsRemaining); // mm*ticks/s/(mm/s*steps) = ticks/step
        limitInterval = RMath::max(axisInterval[X_AXIS],limitInterval);
    }
    else axisInterval[X_AXIS] = 0;
    if(isYMove())
    {
        axisInterval[Y_AXIS] = fabs(axis_diff[Y_AXIS])*F_CPU/(Printer::maxFeedrate[Y_AXIS]*stepsRemaining);
        limitInterval = RMath::max(axisInterval[Y_AXIS],limitInterval);
    }
    else axisInterval[Y_AXIS] = 0;
    if(isZMove())   // normally no move in z direction
    {
        axisInterval[Z_AXIS] = fabs((float)axis_diff[Z_AXIS])*(float)F_CPU/(float)(Printer::maxFeedrate[Z_AXIS]*stepsRemaining); // must prevent overflow!
        limitInterval = RMath::max(axisInterval[Z_AXIS],limitInterval);
    }
    else axisInterval[Z_AXIS] = 0;
    if(isEMove())
    {
        axisInterval[E_AXIS] = fabs(axis_diff[E_AXIS])*F_CPU/(Printer::maxFeedrate[E_AXIS]*stepsRemaining);
        limitInterval = RMath::max(axisInterval[E_AXIS],limitInterval);
    }
    else axisInterval[E_AXIS] = 0;
	
    fullInterval = limitInterval = limitInterval>LIMIT_INTERVAL ? limitInterval : LIMIT_INTERVAL; // This is our target speed
    // new time at full speed = limitInterval*p->stepsRemaining [ticks]
    timeForMove = (float)limitInterval * (float)stepsRemaining; // for large z-distance this overflows with long computation
    float inv_time_s = (float)F_CPU / timeForMove;
    if(isXMove())
    {
        axisInterval[X_AXIS] = timeForMove / delta[X_AXIS];
        speedX = axis_diff[X_AXIS] * inv_time_s;
        if(isXNegativeMove()) speedX = -speedX;
    }
    else speedX = 0;
    if(isYMove())
    {
        axisInterval[Y_AXIS] = timeForMove/delta[Y_AXIS];
        speedY = axis_diff[Y_AXIS] * inv_time_s;
        if(isYNegativeMove()) speedY = -speedY;
    }
    else speedY = 0;
    if(isZMove())
    {
        axisInterval[Z_AXIS] = timeForMove/delta[Z_AXIS];
        speedZ = axis_diff[Z_AXIS] * inv_time_s;
        if(isZNegativeMove()) speedZ = -speedZ;
    }
    else speedZ = 0;
    if(isEMove())
    {
        axisInterval[E_AXIS] = timeForMove/delta[E_AXIS];
        speedE = axis_diff[E_AXIS] * inv_time_s;
        if(isENegativeMove()) speedE = -speedE;
    }

    fullSpeed = distance * inv_time_s;
    //long interval = axis_interval[primary_axis]; // time for every step in ticks with full speed
    //If acceleration is enabled, do some Bresenham calculations depending on which axis will lead it.
#ifdef RAMP_ACCELERATION
    // slowest time to accelerate from v0 to limitInterval determines used acceleration
    // t = (v_end-v_start)/a
    float slowest_axis_plateau_time_repro = 1e15; // repro to reduce division Unit: 1/s
    unsigned long *accel = (isEPositiveMove() ?  Printer::maxPrintAccelerationStepsPerSquareSecond : Printer::maxTravelAccelerationStepsPerSquareSecond);
    for(uint8_t i=0; i < 4 ; i++)
    {
        if(isMoveOfAxis(i))
            // v = a * t => t = v/a = F_CPU/(c*a) => 1/t = c*a/F_CPU
            slowest_axis_plateau_time_repro = RMath::min(slowest_axis_plateau_time_repro,(float)axisInterval[i] * (float)accel[i]); //  steps/s^2 * step/tick  Ticks/s^2
    }
    // Errors for delta move are initialized in timer (except extruder)
    error[0] = error[1] = error[2] = delta[primaryAxis] >> 1;
    invFullSpeed = 1.0/fullSpeed;
    accelerationPrim = slowest_axis_plateau_time_repro / axisInterval[primaryAxis]; // a = v/t = F_CPU/(c*t): Steps/s^2
    //Now we can calculate the new primary axis acceleration, so that the slowest axis max acceleration is not violated
    fAcceleration = 262144.0*(float)accelerationPrim/F_CPU; // will overflow without float!
    accelerationDistance2 = 2.0*distance*slowest_axis_plateau_time_repro*fullSpeed/((float)F_CPU); // mm^2/s^2
    startSpeed = endSpeed = minSpeed = safeSpeed();
    // Can accelerate to full speed within the line
    if (startSpeed * startSpeed + accelerationDistance2 >= fullSpeed * fullSpeed)
        setNominalMove();
	
    vMax = F_CPU / fullInterval; // maximum steps per second, we can reach
    // if(p->vMax>46000)  // gets overflow in N computation
    //   p->vMax = 46000;
    //p->plateauN = (p->vMax*p->vMax/p->accelerationPrim)>>1;

    updateTrapezoids();
    // how much steps on primary axis do we need to reach target feedrate
    //p->plateauSteps = (long) (((float)p->acceleration *0.5f / slowest_axis_plateau_time_repro + p->vMin) *1.01f/slowest_axis_plateau_time_repro);
#endif
	
    // Correct integers for fixed point math used in bresenham_step
    if(fullInterval<MAX_HALFSTEP_INTERVAL || critical)
        halfStep = 4;
    else
    {
        halfStep = 1;
        error[X_AXIS] = error[Y_AXIS] = error[Z_AXIS] = error[E_AXIS] = delta[primaryAxis];
    }
#ifdef DEBUG_STEPCOUNT
	// Set in delta move calculation
    totalStepsRemaining = delta[X_AXIS]+delta[Y_AXIS]+delta[Z_AXIS];
#endif
#ifdef DEBUG_QUEUE_MOVE
    if(Printer::debugEcho())
    {
        logLine();
        Com::printFLN(Com::tDBGLimitInterval, limitInterval);
        Com::printFLN(Com::tDBGMoveDistance, distance);
        Com::printFLN(Com::tDBGCommandedFeedrate, Printer::feedrate);
        Com::printFLN(Com::tDBGConstFullSpeedMoveTime, timeForMove);
    }
#endif
    // Make result permanent
    if (pathOptimize) waitRelax = 70;
    pushLine();
}

/**
 This is the path planner.
 
 It goes from the last entry and tries to increase the end speed of previous moves in a fashion that the maximum jerk
 is never exceeded. If a segment with reached maximum speed is met, the planner stops. Everything left from this
 is already optimal from previous updates.
 The first 2 entries in the queue are not checked. The first is the one that is already in print and the following will likely become active.
 
 The method is called before lines_count is increased!
 */
void PrintLine::updateTrapezoids()
{
    uint8_t first = linesWritePos;
    PrintLine *firstLine;
    PrintLine *act = &lines[linesWritePos];
    //BEGIN_INTERRUPT_PROTECTED;
    uint8_t maxfirst = linesPos; // first non fixed segment
    if(maxfirst != linesWritePos)
        nextPlannerIndex(maxfirst); // don't touch the line printing
    // Now ignore enough segments to gain enough time for path planning
    int32_t timeleft = 0;
    // Skip as many stored moves as needed to gain enough time for computation
    millis_t minTime = 4500L * RMath::min(MOVE_CACHE_SIZE,10);
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
    //END_INTERRUPT_PROTECTED;
    uint8_t previousIndex = linesWritePos;
    previousPlannerIndex(previousIndex);
    PrintLine *previous = &lines[previousIndex];

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

inline void PrintLine::computeMaxJunctionSpeed(PrintLine *previous,PrintLine *current)
{
    // First we compute the normalized jerk for speed 1
    float dx = current->speedX-previous->speedX;
    float dy = current->speedY-previous->speedY;
    float factor = 1;
    float jerk = sqrt(dx*dx + dy*dy);
    if(jerk>Printer::maxJerk)
        factor = Printer::maxJerk / jerk;

    if((previous->dir | current->dir) & 64)
    {
        float dz = fabs(current->speedZ - previous->speedZ);
        if(dz>Printer::maxZJerk)
            factor = RMath::min(factor,Printer::maxZJerk / dz);
    }

    float eJerk = fabs(current->speedE - previous->speedE);
    if(eJerk > Printer::Extruder_maxStartFeedrate)
        factor = RMath::min(factor,Printer::Extruder_maxStartFeedrate / eJerk);
    previous->maxJunctionSpeed = RMath::min(previous->fullSpeed * factor,current->fullSpeed);

}

/** Update parameter used by updateTrapezoids
 
 Computes the acceleration/decelleration steps and advanced parameter associated.
 */
void PrintLine::updateStepsParameter()
{
    if(areParameterUpToDate() || isWarmUp()) return;
    float startFactor = startSpeed * invFullSpeed;
    float endFactor   = endSpeed   * invFullSpeed;
    vStart = vMax * startFactor; //starting speed
    vEnd   = vMax * endFactor;
    uint64_t vmax2 = static_cast<uint64_t>(vMax) * static_cast<uint64_t>(vMax);
    accelSteps = ((vmax2 - static_cast<uint64_t>(vStart) * static_cast<uint64_t>(vStart)) / (accelerationPrim<<1)) + 1; // Always add 1 for missing precision
    decelSteps = ((vmax2 - static_cast<uint64_t>(vEnd) * static_cast<uint64_t>(vEnd))  /(accelerationPrim<<1)) + 1;
	
#ifdef USE_ADVANCE
#ifdef ENABLE_QUADRATIC_ADVANCE
    advanceStart = (float)advanceFull*startFactor * startFactor;
    advanceEnd   = (float)advanceFull*endFactor   * endFactor;
#endif
#endif
    if(accelSteps+decelSteps >= stepsRemaining)   // can't reach limit speed
    {
        uint16_t red = (accelSteps+decelSteps + 2 - stepsRemaining) >> 1;
        accelSteps = accelSteps-RMath::min(accelSteps,red);
        decelSteps = decelSteps-RMath::min(decelSteps,red);
    }
    setParameterUpToDate();
#ifdef DEBUG_QUEUE_MOVE
    if(Printer::debugEcho())
    {
        Com::printFLN(Com::tDBGId,(int)this);
        Com::printF(Com::tDBGVStartEnd,(long)vStart);
        Com::printFLN(Com::tSlash,(long)vEnd);
        Com::printF(Com::tDBAccelSteps,(long)accelSteps);
        Com::printF(Com::tSlash,(long)decelSteps);
        Com::printFLN(Com::tSlash,(long)stepsRemaining);
        Com::printF(Com::tDBGStartEndSpeed,startSpeed,1);
        Com::printFLN(Com::tSlash,endSpeed,1);
        Com::printFLN(Com::tDBGFlags,flags);
        Com::printFLN(Com::tDBGJoinFlags,joinFlags);
    }
#endif
}

/**
 Compute the maximum speed from the last entered move.
 The backwards planner traverses the moves from last to first looking at deceleration. The RHS of the accelerate/decelerate ramp.
 
 start = last line inserted
 last = last element until we check
 */
inline void PrintLine::backwardPlanner(uint8_t start,uint8_t last)
{
    PrintLine *act = &lines[start],*previous;
    float lastJunctionSpeed = act->endSpeed; // Start always with safe speed
	
    //PREVIOUS_PLANNER_INDEX(last); // Last element is already fixed in start speed
    while(start != last)
    {
        previousPlannerIndex(start);
        previous = &lines[start];
        // Avoid speed calc once crusing in split delta move
#if NONLINEAR_SYSTEM
        if (previous->moveID == act->moveID && lastJunctionSpeed == previous->maxJunctionSpeed)
        {
            act->startSpeed = RMath::max(act->minSpeed,previous->endSpeed = lastJunctionSpeed);
            previous->invalidateParameter();
            act->invalidateParameter();
        }
#endif
		
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
                previous->endSpeed = RMath::max(previous->minSpeed,previous->maxJunctionSpeed); // possibly unneeded???
            }
            // If actual line start speed has not been updated to maximum speed then do it now
            if(act->startSpeed != previous->maxJunctionSpeed)
            {
                act->startSpeed = RMath::max(act->minSpeed,previous->maxJunctionSpeed); // possibly unneeded???
                act->invalidateParameter();
            }
            lastJunctionSpeed = previous->endSpeed;
        }
        else
        {
            // Block prev end and act start as calculated speed and recalculate plateau speeds (which could move the speed higher again)
            act->startSpeed = RMath::max(act->minSpeed,lastJunctionSpeed);
            lastJunctionSpeed = previous->endSpeed = RMath::max(lastJunctionSpeed,previous->minSpeed);
            previous->invalidateParameter();
            act->invalidateParameter();
        }
        act = previous;
    } // while loop
}

void PrintLine::forwardPlanner(uint8_t first)
{
    PrintLine *act;
    PrintLine *next = &lines[first];
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
        // Avoid speed calc once crusing in split delta move
#if NONLINEAR_SYSTEM
        if (act->moveID == next->moveID && act->endSpeed == act->maxJunctionSpeed)
        {
            act->startSpeed = leftSpeed;
            leftSpeed       = act->endSpeed;
            act->setEndSpeedFixed(true);
            next->setStartSpeedFixed(true);
            continue;
        }
#endif
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
            next->startSpeed = leftSpeed = RMath::max(RMath::min(act->endSpeed,act->maxJunctionSpeed),next->minSpeed);
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
            act->endSpeed = RMath::max(act->minSpeed,vmaxRight);
            next->startSpeed = leftSpeed = RMath::max(RMath::min(act->endSpeed,act->maxJunctionSpeed),next->minSpeed);
            next->setStartSpeedFixed(true);
        }
    } // While
    next->startSpeed = RMath::max(next->minSpeed,leftSpeed); // This is the new segment, which is updated anyway, no extra flag needed.
}


inline float PrintLine::safeSpeed()
{
    float safe(Printer::maxJerk * 0.5);
#if DRIVE_SYSTEM != 3
    if(isZMove())
    {
        if(primaryAxis == Z_AXIS)
        {
            safe = Printer::maxZJerk*0.5*fullSpeed/fabs(speedZ);
        }
        else if(fabs(speedZ) > Printer::maxZJerk * 0.5)
            safe = RMath::min(safe,Printer::maxZJerk * 0.5 * fullSpeed / fabs(speedZ));
    }
#endif
    if(isEMove())
    {
        if(isXYZMove())
            safe = RMath::min(safe,0.5*Printer::Extruder_maxStartFeedrate*fullSpeed/fabs(speedE));
        else
            safe = 0.5*Printer::Extruder_maxStartFeedrate; // This is a retraction move
    }
    if(primaryAxis == X_AXIS || primaryAxis == Y_AXIS) // enforce minimum speed for numerical stability of explicit speed integration
        safe = RMath::max(Printer::minimumSpeed,safe);
    else if(primaryAxis == Z_AXIS)
    {
        safe = RMath::max(Printer::minimumZSpeed,safe);
    }
    return RMath::min(safe,fullSpeed);
}


/** Check if move is new. If it is insert some dummy moves to allow the path optimizer to work since it does
 not act on the first two moves in the queue. The stepper timer will spot these moves and leave some time for
 processing.
 */
uint8_t PrintLine::insertWaitMovesIfNeeded(uint8_t pathOptimize, uint8_t waitExtraLines)
{
    if(linesCount==0 && waitRelax==0 && pathOptimize)   // First line after some time - warmup needed
    {
        uint8_t w = 4;
        while(w--)
        {
            PrintLine *p = getNextWriteLine();
            p->flags = FLAG_WARMUP;
            p->joinFlags = FLAG_JOIN_STEPPARAMS_COMPUTED | FLAG_JOIN_END_FIXED | FLAG_JOIN_START_FIXED;
            p->dir = 0;
            p->setWaitForXLinesFilled(w + waitExtraLines);
            p->setWaitTicks(25000);
            pushLine();
        }
        return 1;
    }
    return 0;
}
void PrintLine::logLine()
{
#ifdef DEBUG_QUEUE_MOVE
    Com::printFLN(Com::tDBGId,(int)this);
    Com::printArrayFLN(Com::tDBGDelta,delta);
    Com::printFLN(Com::tDBGDir,dir);
    Com::printFLN(Com::tDBGFlags,flags);
    Com::printFLN(Com::tDBGFullSpeed,fullSpeed);
    Com::printFLN(Com::tDBGVMax,(long)vMax);
    Com::printFLN(Com::tDBGAcceleration,accelerationDistance2);
    Com::printFLN(Com::tDBGAccelerationPrim,(long)accelerationPrim);
    Com::printFLN(Com::tDBGRemainingSteps,stepsRemaining);
#ifdef USE_ADVANCE
#ifdef ENABLE_QUADRATIC_ADVANCE
    Com::printFLN(Com::tDBGAdvanceFull,advanceFull>>16);
    Com::printFLN(Com::tDBGAdvanceRate,advanceRate);
#endif
#endif
#endif // DEBUG_QUEUE_MOVE
}

void PrintLine::waitForXFreeLines(uint8_t b)
{
    while(linesCount+b>MOVE_CACHE_SIZE)   // wait for a free entry in movement cache
    {
       // GCode::readFromSerial();
       // Commands::checkForPeriodicalActions();
    }
}



#if ARC_SUPPORT
// Arc function taken from grbl
// The arc is approximated by generating a huge number of tiny, linear segments. The length of each
// segment is configured in settings.mm_per_arc_segment.
void PrintLine::arc(float *position, float *target, float *offset, float radius, uint8_t isclockwise)
{
    //   int acceleration_manager_was_enabled = plan_is_acceleration_manager_enabled();
    //   plan_set_acceleration_manager_enabled(false); // disable acceleration management for the duration of the arc
    float center_axis0 = position[0] + offset[0];
    float center_axis1 = position[1] + offset[1];
    float linear_travel = 0; //target[axis_linear] - position[axis_linear];
    float extruder_travel = (Printer::destinationSteps[E_AXIS]-Printer::currentPositionSteps[E_AXIS])*Printer::invAxisStepsPerMM[E_AXIS];
    float r_axis0 = -offset[0];  // Radius vector from center to current location
    float r_axis1 = -offset[1];
    float rt_axis0 = target[0] - center_axis0;
    float rt_axis1 = target[1] - center_axis1;
    long xtarget = Printer::destinationSteps[X_AXIS];
    long ytarget = Printer::destinationSteps[Y_AXIS];
    long ztarget = Printer::destinationSteps[Z_AXIS];
    long etarget = Printer::destinationSteps[E_AXIS];
	
    // CCW angle between position and target from circle center. Only one atan2() trig computation required.
    float angular_travel = atan2(r_axis0*rt_axis1-r_axis1*rt_axis0, r_axis0*rt_axis0+r_axis1*rt_axis1);
    if (angular_travel < 0)
    {
        angular_travel += 2*M_PI;
    }
    if (isclockwise)
    {
        angular_travel -= 2*M_PI;
    }
	
    float millimeters_of_travel = fabs(angular_travel)*radius; //hypot(angular_travel*radius, fabs(linear_travel));
    if (millimeters_of_travel < 0.001)
    {
        return;
    }
    //uint16_t segments = (radius>=BIG_ARC_RADIUS ? floor(millimeters_of_travel/MM_PER_ARC_SEGMENT_BIG) : floor(millimeters_of_travel/MM_PER_ARC_SEGMENT));
    // Increase segment size if printing faster then computation speed allows
    uint16_t segments = (Printer::feedrate>60 ? floor(millimeters_of_travel/RMath::min(MM_PER_ARC_SEGMENT_BIG,Printer::feedrate*0.01666*MM_PER_ARC_SEGMENT)) : floor(millimeters_of_travel/MM_PER_ARC_SEGMENT));
    if(segments == 0) segments = 1;
    /*
	 // Multiply inverse feed_rate to compensate for the fact that this movement is approximated
	 // by a number of discrete segments. The inverse feed_rate should be correct for the sum of
	 // all segments.
	 if (invert_feed_rate) { feed_rate *= segments; }
	 */
    float theta_per_segment = angular_travel/segments;
    float linear_per_segment = linear_travel/segments;
    float extruder_per_segment = extruder_travel/segments;
	
    /* Vector rotation by transformation matrix: r is the original vector, r_T is the rotated vector,
	 and phi is the angle of rotation. Based on the solution approach by Jens Geisler.
	 r_T = [cos(phi) -sin(phi);
	 sin(phi)  cos(phi] * r ;
	 
	 For arc generation, the center of the circle is the axis of rotation and the radius vector is
	 defined from the circle center to the initial position. Each line segment is formed by successive
	 vector rotations. This requires only two cos() and sin() computations to form the rotation
	 matrix for the duration of the entire arc. Error may accumulate from numerical round-off, since
	 all double numbers are single precision on the Arduino. (True double precision will not have
	 round off issues for CNC applications.) Single precision error can accumulate to be greater than
	 tool precision in some cases. Therefore, arc path correction is implemented.
	 
	 Small angle approximation may be used to reduce computation overhead further. This approximation
	 holds for everything, but very small circles and large mm_per_arc_segment values. In other words,
	 theta_per_segment would need to be greater than 0.1 rad and N_ARC_CORRECTION would need to be large
	 to cause an appreciable drift error. N_ARC_CORRECTION~=25 is more than small enough to correct for
	 numerical drift error. N_ARC_CORRECTION may be on the order a hundred(s) before error becomes an
	 issue for CNC machines with the single precision Arduino calculations.
	 
	 This approximation also allows mc_arc to immediately insert a line segment into the planner
	 without the initial overhead of computing cos() or sin(). By the time the arc needs to be applied
	 a correction, the planner should have caught up to the lag caused by the initial mc_arc overhead.
	 This is important when there are successive arc motions.
	 */
    // Vector rotation matrix values
    float cos_T = 1-0.5*theta_per_segment*theta_per_segment; // Small angle approximation
    float sin_T = theta_per_segment;
	
    float arc_target[4];
    float sin_Ti;
    float cos_Ti;
    float r_axisi;
    uint16_t i;
    int8_t count = 0;
	
    // Initialize the linear axis
    //arc_target[axis_linear] = position[axis_linear];
	
    // Initialize the extruder axis
    arc_target[3] = Printer::currentPositionSteps[3]*Printer::invAxisStepsPerMM[3];
	
    for (i = 1; i<segments; i++)
    {
        // Increment (segments-1)
		
        if((count & 3) == 0)
        {
            GCode::readFromSerial();
            Commands::checkForPeriodicalActions();
            UI_MEDIUM; // do check encoder
        }
		
        if (count < N_ARC_CORRECTION)  //25 pieces
        {
            // Apply vector rotation matrix
            r_axisi = r_axis0*sin_T + r_axis1*cos_T;
            r_axis0 = r_axis0*cos_T - r_axis1*sin_T;
            r_axis1 = r_axisi;
            count++;
        }
        else
        {
            // Arc correction to radius vector. Computed only every N_ARC_CORRECTION increments.
            // Compute exact location by applying transformation matrix from initial radius vector(=-offset).
            cos_Ti  = cos(i*theta_per_segment);
            sin_Ti  = sin(i*theta_per_segment);
            r_axis0 = -offset[0]*cos_Ti + offset[1]*sin_Ti;
            r_axis1 = -offset[0]*sin_Ti - offset[1]*cos_Ti;
            count = 0;
        }
		
        // Update arc_target location
        arc_target[0] = center_axis0 + r_axis0;
        arc_target[1] = center_axis1 + r_axis1;
        //arc_target[axis_linear] += linear_per_segment;
        arc_target[3] += extruder_per_segment;
        Printer::moveToReal(arc_target[0],arc_target[1],IGNORE_COORDINATE,arc_target[3],IGNORE_COORDINATE);
    }
    // Ensure last segment arrives at target location.
    Printer::moveToReal(target[0],target[1],IGNORE_COORDINATE,target[3],IGNORE_COORDINATE);
}
#endif


/**
 Moves the stepper motors one step. If the last step is reached, the next movement is started.
 The function must be called from a timer loop. It returns the time for the next call.
 
 Normal non delta algorithm
 */
int lastblk=-1;
long cur_errupd;
long PrintLine::bresenhamStep() // version for cartesian printer
{
#if CPU_ARCH==ARCH_ARM
    if(!PrintLine::nlFlag)
#else
		if(cur == NULL)
#endif
		{
			ANALYZER_ON(ANALYZER_CH0);
			setCurrentLine();
			if(cur->isBlocked())   // This step is in computation - shouldn't happen
			{
				/*if(lastblk!=(int)cur) // can cause output errors!
				 {
				 HAL::allowInterrupts();
				 lastblk = (int)cur;
				 Com::printFLN(Com::tBLK,lines_count);
				 }*/
				cur = NULL;
#if CPU_ARCH==ARCH_ARM
				PrintLine::nlFlag = false;
#endif
				return 2000;
			}
			//HAL::allowInterrupts();
			lastblk = -1;
#ifdef INCLUDE_DEBUG_NO_MOVE
			if(Printer::debugNoMoves())   // simulate a move, but do nothing in reality
			{
				removeCurrentLineForbidInterrupt();
				return 1000;
			}
#endif
			ANALYZER_OFF(ANALYZER_CH0);
			if(cur->isWarmUp())
			{
				// This is a warmup move to initalize the path planner correctly. Just waste
				// a bit of time to get the planning up to date.
				if(linesCount<=cur->getWaitForXLinesFilled())
				{
					cur = NULL;
#if CPU_ARCH==ARCH_ARM
					PrintLine::nlFlag = false;
#endif
					return 2000;
				}
				long wait = cur->getWaitTicks();
				removeCurrentLineForbidInterrupt();
				return(wait); // waste some time for path optimization to fill up
			} // End if WARMUP
			//Only enable axis that are moving. If the axis doesn't need to move then it can stay disabled depending on configuration.

			//if(cur->isXMove()) Printer::enableXStepper();
			//if(cur->isYMove()) Printer::enableYStepper();

			/*if(cur->isZMove())
			{
				Printer::enableZStepper();
			}
			if(cur->isEMove()) Extruder::enable();
			 */
			cur->fixStartAndEndSpeed();
			//HAL::allowInterrupts();
			cur_errupd = (cur->isFullstepping() ? cur->delta[cur->primaryAxis] : cur->delta[cur->primaryAxis]<<1);;
			if(!cur->areParameterUpToDate())  // should never happen, but with bad timings???
			{
				cur->updateStepsParameter();
			}
			Printer::vMaxReached = cur->vStart;
			Printer::stepNumber=0;
			Printer::timer = 0;
			//HAL::forbidInterrupts();
			//Determine direction of movement,check if endstop was hit

			//Printer::setXDirection(cur->isXPositiveMove());
			//Printer::setYDirection(cur->isYPositiveMove());

			long gdx = (cur->dir & 1 ? cur->delta[0] : -cur->delta[0]); // Compute signed difference in steps
			long gdy = (cur->dir & 2 ? cur->delta[1] : -cur->delta[1]);
			//Printer::setXDirection(gdx+gdy>=0);

			//Printer::setZDirection(cur->isZPositiveMove());

			//Extruder::setDirection(cur->isEPositiveMove());

			if(Printer::wasLastHalfstepping && cur->isFullstepping())   // Switch halfstepping -> full stepping
			{
				Printer::wasLastHalfstepping = 0;
				return Printer::interval+Printer::interval+Printer::interval; // Wait an other 150% from last half step to make the 100% full
			}
			else if(!Printer::wasLastHalfstepping && !cur->isFullstepping())     // Switch full to half stepping
			{
				Printer::wasLastHalfstepping = 1;
			}
			else
				return Printer::interval; // Wait an other 50% from last step to make the 100% full
		} // End cur=0
    //HAL::allowInterrupts();
    /* For halfstepping, we divide the actions into even and odd actions to split
	 time used per loop. */
    uint8_t doEven = cur->halfStep & 6;
    uint8_t doOdd = cur->halfStep & 5;
    if(cur->halfStep!=4) cur->halfStep = 3-(cur->halfStep);
    //HAL::forbidInterrupts();
    if(doEven) cur->checkEndstops();
    uint8_t max_loops = RMath::min((long)Printer::stepsPerTimerCall,(long)cur->stepsRemaining);
    if(cur->stepsRemaining>0)
    {
        for(uint8_t loop=0; loop<max_loops; loop++)
        {
            ANALYZER_ON(ANALYZER_CH1);
#if STEPPER_HIGH_DELAY+DOUBLE_STEP_DELAY > 0
            if(loop>0)
                HAL::delayMicroseconds(STEPPER_HIGH_DELAY+DOUBLE_STEP_DELAY);
#endif
            if(cur->isEMove())
            {
                if((cur->error[E_AXIS] -= cur->delta[E_AXIS]) < 0)
                {
                        //Extruder::step();
                    cur->error[E_AXIS] += cur_errupd;
                }
            }
            if(cur->isXMove())
            {
                if((cur->error[X_AXIS] -= cur->delta[X_AXIS]) < 0)
                {
                    cur->startXStep();
                    cur->error[X_AXIS] += cur_errupd;
                }
            }
            if(cur->isYMove())
            {
                if((cur->error[Y_AXIS] -= cur->delta[Y_AXIS]) < 0)
                {
                    cur->startYStep();
                    cur->error[Y_AXIS] += cur_errupd;
                }
            }
			
            if(cur->isZMove())
            {
                if((cur->error[Z_AXIS] -= cur->delta[Z_AXIS]) < 0)
                {
                    cur->startZStep();
                    cur->error[Z_AXIS] += cur_errupd;
#ifdef DEBUG_STEPCOUNT
                    cur->totalStepsRemaining--;
#endif
                }
            }
            Printer::insertStepperHighDelay();
                //Extruder::unstep();
            Printer::endXYZSteps();
        } // for loop
        if(doOdd)  // Update timings
        {
            //HAL::allowInterrupts(); // Allow interrupts for other types, timer1 is still disabled
#ifdef RAMP_ACCELERATION
            //If acceleration is enabled on this move and we are in the acceleration segment, calculate the current interval
            if (cur->moveAccelerating())   // we are accelerating
            {
				
                //Printer::vMaxReached = HAL::ComputeV(Printer::timer,cur->fAcceleration)+cur->vStart;
				Printer::vMaxReached = ((Printer::timer>>8)*(cur->fAcceleration)+cur->vStart)>>10;

                if(Printer::vMaxReached>cur->vMax) Printer::vMaxReached = cur->vMax;
                unsigned int v = Printer::updateStepsPerTimerCall(Printer::vMaxReached);
                Printer::interval = F_CPU/v;
                Printer::timer+=Printer::interval;
                cur->updateAdvanceSteps(Printer::vMaxReached,max_loops,true);
            }
            else if (cur->moveDecelerating())     // time to slow down
            {
                unsigned int v = ((Printer::timer>>8)*cur->fAcceleration)>>10;
				
                if (v > Printer::vMaxReached)   // if deceleration goes too far it can become too large
                    v = cur->vEnd;
                else
                {
                    v=Printer::vMaxReached - v;
                    if (v<cur->vEnd) v = cur->vEnd; // extra steps at the end of desceleration due to rounding erros
                }
                cur->updateAdvanceSteps(v,max_loops,false); // needs original v
                v = Printer::updateStepsPerTimerCall(v);
                Printer::interval = F_CPU/v;
                Printer::timer += Printer::interval;
            }
            else // full speed reached
            {
                cur->updateAdvanceSteps((!cur->accelSteps ? cur->vMax : Printer::vMaxReached),0,true);
                // constant speed reached
                if(cur->vMax>STEP_DOUBLER_FREQUENCY)
                {
#if ALLOW_QUADSTEPPING
                    if(cur->vMax>STEP_DOUBLER_FREQUENCY*2)
                    {
                        Printer::stepsPerTimerCall = 4;
                        Printer::interval = cur->fullInterval << 2;
                    }
                    else
                    {
                        Printer::stepsPerTimerCall = 2;
                        Printer::interval = cur->fullInterval << 1;
                    }
#else
                    Printer::stepsPerTimerCall = 2;
                    Printer::interval = cur->fullInterval << 1;
#endif
                }
                else
                {
                    Printer::stepsPerTimerCall = 1;
                    Printer::interval = cur->fullInterval;
                }
            }
#else
            Printer::stepsPerTimerCall = 1;
            Printer::interval = cur->fullInterval; // without RAMPS always use full speed
#endif // RAMP_ACCELERATION
        } // doOdd
        if(doEven)
        {
            Printer::stepNumber += max_loops;
            cur->stepsRemaining -= max_loops;
        }
		
    } // stepsRemaining
    long interval;
    if(!cur->isFullstepping()) interval = (Printer::interval>>1); // time to come back
    else interval = Printer::interval;
    if(doEven && (cur->stepsRemaining <= 0 || cur->isNoMove()))   // line finished
    {
#ifdef DEBUG_STEPCOUNT
        if(cur->totalStepsRemaining)
        {
            Com::printF(Com::tDBGMissedSteps,cur->totalStepsRemaining);
            Com::printFLN(Com::tComma,cur->stepsRemaining);
        }
#endif
        removeCurrentLineForbidInterrupt();
        Printer::disableAllowedStepper();

        interval = Printer::interval = interval >> 1; // 50% of time to next call to do cur=0

    } // Do even
    /*if(FEATURE_BABYSTEPPING && Printer::zBabystepsMissing)
    {
        Printer::zBabystep();
    }*/
    return interval;
}

