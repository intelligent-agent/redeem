//
//  PathPlanner.h
//  PathPlanner
//
//  Created by Mathieu on 29.05.14.
//  Copyright (c) 2014 Xwaves. All rights reserved.
//

#ifndef __PathPlanner__PathPlanner__
#define __PathPlanner__PathPlanner__

#include <iostream>
#include <atomic>
#include <thread>
#include <mutex>
#include <string.h>
#include <strings.h>
#include "PruTimer.h"

#define NUM_AXIS 4
#define X_AXIS 0
#define Y_AXIS 1
#define Z_AXIS 2
#define E_AXIS 3
#define H_AXIS 4

#define FLAG_WARMUP 1
#define FLAG_NOMINAL 2
#define FLAG_DECELERATING 4
#define FLAG_ACCELERATION_ENABLED 8
#define FLAG_CHECK_ENDSTOPS 16
#define FLAG_SKIP_ACCELERATING 32
#define FLAG_SKIP_DEACCELERATING 64
#define FLAG_BLOCKED 128

/** Are the step parameter computed */
#define FLAG_JOIN_STEPPARAMS_COMPUTED 1
/** The right speed is fixed. Don't check this block or any block to the left. */
#define FLAG_JOIN_END_FIXED 2
/** The left speed is fixed. Don't check left block. */
#define FLAG_JOIN_START_FIXED 4
/** Start filament retraction at move start */
#define FLAG_JOIN_START_RETRACT 8
/** Wait for filament pushback, before ending move */
#define FLAG_JOIN_END_RETRACT 16
/** Disable retract for this line */
#define FLAG_JOIN_NO_RETRACT 32
/** Wait for the extruder to finish it's up movement */
#define FLAG_JOIN_WAIT_EXTRUDER_UP 64
/** Wait for the extruder to finish it's down movement */
#define FLAG_JOIN_WAIT_EXTRUDER_DOWN 128

#define MOVE_CACHE_SIZE 16

typedef struct SteppersCommand {
	uint8_t     step  ;              //Steppers are defined as 0b000HEZYX - A 1 for a stepper means we will do a step for this stepper
	uint8_t     direction ;          //Steppers are defined as 0b000HEZYX - Direction for each stepper
	uint16_t    options   ;          //Options for the move - If the first bit is set to 1, then the stepper has the cancellable
//option meaning that as soon as an endstop is hit, all the moves in the DDR are removed and canceled without making the steppers to move.
	uint32_t    delay    ;           //number of cycle to wait (this is the # of PRU click cycles)
} SteppersCommand;

static_assert(sizeof(SteppersCommand)==8,"Invalid stepper command size");

class Path {
private:
	unsigned int joinFlags;
	std::atomic_uint_fast32_t flags;
	
	unsigned int primaryAxis;
    int timeInTicks;
    unsigned int dir;                       ///< Direction of movement. 1 = X+, 2 = Y+, 4= Z+, values can be combined.
    int delta[NUM_AXIS];                  ///< Steps we want to move.
    int error[NUM_AXIS];                  ///< Error calculation for Bresenham algorithm
    float speedX;                   ///< Speed in x direction at fullInterval in mm/s
    float speedY;                   ///< Speed in y direction at fullInterval in mm/s
    float speedZ;                   ///< Speed in z direction at fullInterval in mm/s
    float speedE;                   ///< Speed in E direction at fullInterval in mm/s
    float fullSpeed;                ///< Desired speed mm/s
    float invFullSpeed;             ///< 1.0/fullSpeed for fatser computation
    float accelerationDistance2;             ///< Real 2.0*distanceÜacceleration mm²/s²
    float maxJunctionSpeed;         ///< Max. junction speed between this and next segment
    float startSpeed;               ///< Staring speed in mm/s
    float endSpeed;                 ///< Exit speed in mm/s
    float minSpeed;
    float distance;
    unsigned int fullInterval;     ///< interval at full speed in ticks/step.
    unsigned int accelSteps;        ///< How much steps does it take, to reach the plateau.
    unsigned int decelSteps;        ///< How much steps does it take, to reach the end speed.
    unsigned int accelerationPrim; ///< Acceleration along primary axis
    unsigned int fAcceleration;    ///< accelerationPrim*262144/F_CPU
    unsigned int vMax;              ///< Maximum reached speed in steps/s.
    unsigned int vStart;            ///< Starting speed in steps/s.
    unsigned int vEnd;              ///< End speed in steps/s
    unsigned int stepsRemaining;            ///< Remaining steps, until move is finished

	
	
	inline bool areParameterUpToDate()
    {
        return joinFlags & FLAG_JOIN_STEPPARAMS_COMPUTED;
    }
    inline void invalidateParameter()
    {
        joinFlags &= ~FLAG_JOIN_STEPPARAMS_COMPUTED;
    }
    inline void setParameterUpToDate()
    {
        joinFlags |= FLAG_JOIN_STEPPARAMS_COMPUTED;
    }
    inline bool isStartSpeedFixed()
    {
        return joinFlags & FLAG_JOIN_START_FIXED;
    }
    inline void setStartSpeedFixed(bool newState)
    {
        joinFlags = (newState ? joinFlags | FLAG_JOIN_START_FIXED : joinFlags & ~FLAG_JOIN_START_FIXED);
    }
    inline void fixStartAndEndSpeed()
    {
        joinFlags |= FLAG_JOIN_END_FIXED | FLAG_JOIN_START_FIXED;
    }
    inline bool isEndSpeedFixed()
    {
        return joinFlags & FLAG_JOIN_END_FIXED;
    }
    inline void setEndSpeedFixed(bool newState)
    {
        joinFlags = (newState ? joinFlags | FLAG_JOIN_END_FIXED : joinFlags & ~FLAG_JOIN_END_FIXED);
    }
    inline bool isWarmUp()
    {
        return flags & FLAG_WARMUP;
    }
    inline uint8_t getWaitForXLinesFilled()
    {
        return primaryAxis;
    }
    inline void setWaitForXLinesFilled(uint8_t b)
    {
        primaryAxis = b;
    }
    inline bool isExtruderForwardMove()
    {
        return (dir & 136)==136;
    }
    inline void block()
    {
        flags |= FLAG_BLOCKED;
    }
    inline void unblock()
    {
        flags &= ~FLAG_BLOCKED;
    }
    inline bool isBlocked()
    {
        return flags & FLAG_BLOCKED;
    }
    inline bool isCheckEndstops()
    {
        return flags & FLAG_CHECK_ENDSTOPS;
    }
    inline bool isNominalMove()
    {
        return flags & FLAG_NOMINAL;
    }
    inline void setNominalMove()
    {
        flags |= FLAG_NOMINAL;
    }

    inline void setXMoveFinished()
    {
        dir&=~16;
    }
    inline void setYMoveFinished()
    {
        dir&=~32;
    }
    inline void setZMoveFinished()
    {
        dir&=~64;
    }
    inline void setXYMoveFinished()
    {
        dir&=~48;
    }
    inline bool isXPositiveMove()
    {
        return (dir & 17)==17;
    }
    inline bool isXNegativeMove()
    {
        return (dir & 17)==16;
    }
    inline bool isYPositiveMove()
    {
        return (dir & 34)==34;
    }
    inline bool isYNegativeMove()
    {
        return (dir & 34)==32;
    }
    inline bool isZPositiveMove()
    {
        return (dir & 68)==68;
    }
    inline bool isZNegativeMove()
    {
        return (dir & 68)==64;
    }
    inline bool isEPositiveMove()
    {
        return (dir & 136)==136;
    }
    inline bool isENegativeMove()
    {
        return (dir & 136)==128;
    }
    inline bool isXMove()
    {
        return (dir & 16);
    }
    inline bool isYMove()
    {
        return (dir & 32);
    }
    inline bool isXOrYMove()
    {
        return dir & 48;
    }
    inline bool isZMove()
    {
        return (dir & 64);
    }
    inline bool isEMove()
    {
        return (dir & 128);
    }
    inline bool isEOnlyMove()
    {
        return (dir & 240)==128;
    }
    inline bool isNoMove()
    {
        return (dir & 240)==0;
    }
    inline bool isXYZMove()
    {
        return dir & 112;
    }
    inline bool isMoveOfAxis(uint8_t axis)
    {
        return (dir & (16<<axis));
    }
    inline void setMoveOfAxis(uint8_t axis)
    {
        dir |= 16<<axis;
    }
    inline void setPositiveDirectionForAxis(uint8_t axis)
    {
        dir |= 1<<axis;
    }
	
	inline bool moveDecelerating(unsigned int stepNumber)
    {
        if(stepNumber <= decelSteps)
        {
            if (!(flags & FLAG_DECELERATING))
            {
                //Printer::timer = 0;
                flags |= FLAG_DECELERATING;
            }
            return true;
        }
        else return false;
    }
	
	inline bool moveAccelerating(unsigned int stepNumber)
    {
        return stepNumber <= accelSteps;
    }
	
	
	void updateStepsParameter();

	
	SteppersCommand *commands;
	
public:
	
	float speed; //Feedrate
	
	float startPos[NUM_AXIS];
	float endPos[NUM_AXIS];
	
	
	
	
	friend class PathPlanner;
};

class PathPlanner {

	void calculateMove(Path* p,float axis_diff[NUM_AXIS]);
	float safeSpeed(Path *p);
	void updateTrapezoids();
	void computeMaxJunctionSpeed(Path *previous,Path *current);
	void backwardPlanner(unsigned int start,unsigned int last);
	void forwardPlanner(unsigned int first);
	
	float maxFeedrate[NUM_AXIS];
	unsigned long maxPrintAccelerationStepsPerSquareSecond[NUM_AXIS];
	unsigned long maxTravelAccelerationStepsPerSquareSecond[NUM_AXIS];
	unsigned long maxAccelerationMMPerSquareSecond[NUM_AXIS];
	unsigned long  maxTravelAccelerationMMPerSquareSecond[NUM_AXIS];
	
	float maxJerk;
	float maxZJerk;
	
	float minimumSpeed;
	float minimumZSpeed;
	float Extruder_maxStartFeedrate;
	float invAxisStepsPerMM[NUM_AXIS];
	unsigned long axisStepsPerMM[NUM_AXIS];

	
	std::atomic_uint_fast32_t linesPos; // Position for executing line movement
	std::atomic_uint_fast32_t linesWritePos; // Position where we write the next cached line move
	std::atomic_uint_fast32_t linesCount;      ///< Number of lines cached 0 = nothing to do.

	Path lines[MOVE_CACHE_SIZE];

	inline void previousPlannerIndex(unsigned int &p)
    {
        p = (p ? p-1 : MOVE_CACHE_SIZE-1);
    }
	inline void nextPlannerIndex(unsigned int& p)
    {
        p = (p == MOVE_CACHE_SIZE - 1 ? 0 : p + 1);
    }
	
	inline void removeCurrentLineForbidInterrupt()
    {
        linesPos++;
        if(linesPos>=MOVE_CACHE_SIZE) linesPos=0;

        --linesCount;
		
    }
	
	std::mutex m;
	std::condition_variable lineAvailable;
	
	std::thread runningThread;
	bool stop;
	
	PruTimer pru;
	void recomputeParameters();
	
public:
	PathPlanner();
	void queueMove(float startPos[NUM_AXIS],float endPos[NUM_AXIS],float speed);
	void run();
	
	void runThread();
	void stopThread(bool join);
	
	void setMaxFeedrates(unsigned long rates[NUM_AXIS]);
	void setAxisStepsPerMM(unsigned long stepPerMM[NUM_AXIS]);
	void setPrintAcceleration(unsigned long accel[NUM_AXIS]);
	void setTravelAcceleration(unsigned long accel[NUM_AXIS]);
	void setMaxJerk(unsigned long maxJerk, unsigned long maxZJerk);
	void setMaximumExtruderStartFeedrate(unsigned long maxstartfeedrate);
	
	void waitUntilFinished();
	
	bool initPRU(const std::string& firmware_stepper, const std::string& firmware_endstops) {
		return pru.initPRU(firmware_stepper, firmware_endstops);
	}
	
	
	virtual ~PathPlanner();

};

#endif /* defined(__PathPlanner__PathPlanner__) */
