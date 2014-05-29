//
//  Path.h
//  PathPlanner
//
//  Created by Mathieu on 29.05.14.
//  Copyright (c) 2014 Xwaves. All rights reserved.
//

#ifndef __PathPlanner__Path__
#define __PathPlanner__Path__

#include <iostream>
#include <stdint.h>
#include "Printer.h"





#define MOVE_CACHE_SIZE 16

/** Marks the first step of a new move */
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

class PrintLine {
	friend class UIDisplay;
#if CPU_ARCH==ARCH_ARM
    static volatile bool nlFlag;
#endif
public:
    static uint8_t linesPos; // Position for executing line movement
    static uint8_t linesWritePos; // Position where we write the next cached line move
    static PrintLine lines[];
    flag8_t joinFlags;
    volatile flag8_t flags;
private:
    flag8_t primaryAxis;
    int32_t timeInTicks;
    flag8_t halfStep;                  ///< 4 = disabled, 1 = halfstep, 2 = fulstep
    flag8_t dir;                       ///< Direction of movement. 1 = X+, 2 = Y+, 4= Z+, values can be combined.
    int32_t delta[4];                  ///< Steps we want to move.
    int32_t error[4];                  ///< Error calculation for Bresenham algorithm
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
    ticks_t fullInterval;     ///< interval at full speed in ticks/step.
    uint16_t accelSteps;        ///< How much steps does it take, to reach the plateau.
    uint16_t decelSteps;        ///< How much steps does it take, to reach the end speed.
    uint32_t accelerationPrim; ///< Acceleration along primary axis
    uint32_t fAcceleration;    ///< accelerationPrim*262144/F_CPU
    speed_t vMax;              ///< Maximum reached speed in steps/s.
    speed_t vStart;            ///< Starting speed in steps/s.
    speed_t vEnd;              ///< End speed in steps/s
#ifdef DEBUG_STEPCOUNT
    int32_t totalStepsRemaining;
#endif
public:
    int32_t stepsRemaining;            ///< Remaining steps, until move is finished
    static PrintLine *cur;
    static volatile uint8_t linesCount; // Number of lines cached 0 = nothing to do
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
    inline void checkEndstops()
    {
       /* if(isCheckEndstops())
        {
            if(isXNegativeMove() && Printer::isXMinEndstopHit())
                setXMoveFinished();
            if(isYNegativeMove() && Printer::isYMinEndstopHit())
                setYMoveFinished();
            if(isXPositiveMove() && Printer::isXMaxEndstopHit())
                setXMoveFinished();
            if(isYPositiveMove() && Printer::isYMaxEndstopHit())
                setYMoveFinished();
        }
		// Test Z-Axis every step if necessary, otherwise it could easyly ruin your printer!
		if(isZNegativeMove() && Printer::isZMinEndstopHit())
			setZMoveFinished();
        if(isZPositiveMove() && Printer::isZMaxEndstopHit())
        {
            setZMoveFinished();
        }
        if(isZPositiveMove() && Printer::isZMaxEndstopHit())
            setZMoveFinished();*/
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
    inline static void resetPathPlanner()
    {
        linesCount = 0;
        linesPos = linesWritePos;
    }
    inline void updateAdvanceSteps(speed_t v,uint8_t max_loops,bool accelerate)
    {
		
    }
    inline bool moveDecelerating()
    {
        if(stepsRemaining <= decelSteps)
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
    inline bool moveAccelerating()
    {
        return Printer::stepNumber <= accelSteps;
    }
    inline bool isFullstepping()
    {
        return halfStep == 4;
    }
    inline void startXStep()
    {
        ANALYZER_ON(ANALYZER_CH6);
        ANALYZER_ON(ANALYZER_CH2);
        WRITE(X_STEP_PIN,HIGH);
		
#ifdef DEBUG_STEPCOUNT
        totalStepsRemaining--;
#endif
		
    }
    inline void startYStep()
    {
        ANALYZER_ON(ANALYZER_CH7);
		
        ANALYZER_ON(ANALYZER_CH3);
        WRITE(Y_STEP_PIN,HIGH);
#ifdef DEBUG_STEPCOUNT
        totalStepsRemaining--;
#endif
    }
    inline void startZStep()
    {
        WRITE(Z_STEP_PIN,HIGH);
    }
    void updateStepsParameter();
    inline float safeSpeed();
    void calculateMove(float axis_diff[],uint8_t pathOptimize);
    void logLine();
    inline long getWaitTicks()
    {
        return timeInTicks;
    }
    inline void setWaitTicks(long wait)
    {
        timeInTicks = wait;
    }
	
    static inline bool hasLines()
    {
        return linesCount;
    }

    static inline void removeCurrentLineForbidInterrupt()
    {
        linesPos++;
        if(linesPos>=MOVE_CACHE_SIZE) linesPos=0;
        cur = NULL;
#if CPU_ARCH==ARCH_ARM
        nlFlag = false;
#endif
      //  HAL::forbidInterrupts();
        --linesCount;

    }
    static inline void pushLine()
    {
        linesWritePos++;
        if(linesWritePos>=MOVE_CACHE_SIZE) linesWritePos = 0;

       // BEGIN_INTERRUPT_PROTECTED
        linesCount++;
       // END_INTERRUPT_PROTECTED
    }
	
    static PrintLine *getNextWriteLine()
    {
        return &lines[linesWritePos];
    }
	
	static inline void setCurrentLine()
    {
        cur = &lines[linesPos];
#if CPU_ARCH==ARCH_ARM
        PrintLine::nlFlag = true;
#endif
    }
	
    static inline void computeMaxJunctionSpeed(PrintLine *previous,PrintLine *current);
    static long bresenhamStep();
    static void waitForXFreeLines(uint8_t b=1);
    static inline void forwardPlanner(uint8_t p);
    static inline void backwardPlanner(uint8_t p,uint8_t last);
    static void updateTrapezoids();
    static uint8_t insertWaitMovesIfNeeded(uint8_t pathOptimize, uint8_t waitExtraLines);
    static void queueCartesianMove(uint8_t check_endstops,uint8_t pathOptimize);
    static void moveRelativeDistanceInSteps(long x,long y,long z,long e,float feedrate,bool waitEnd,bool check_endstop);
    static void moveRelativeDistanceInStepsReal(long x,long y,long z,long e,float feedrate,bool waitEnd);
#if ARC_SUPPORT
    static void arc(float *position, float *target, float *offset, float radius, uint8_t isclockwise);
#endif
    static inline void previousPlannerIndex(uint8_t &p)
    {
        p = (p ? p-1 : MOVE_CACHE_SIZE-1);
    }
    static inline void nextPlannerIndex(uint8_t& p)
    {
        p = (p == MOVE_CACHE_SIZE - 1 ? 0 : p + 1);
    }
};

#endif /* defined(__PathPlanner__Path__) */
