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

#ifndef __PathPlanner__Path__
#define __PathPlanner__Path__

#include "StepperCommand.h"
#include "config.h"
#include "vectorN.h"
#include <array>
#include <assert.h>
#include <atomic>
#include <stddef.h>
#include <stdint.h>
#include <string>
#include <vector>

#define FLAG_WILL_REACH_FULL_SPEED (1 << 0)
#define FLAG_ACCELERATION_ENABLED (1 << 1)
#define FLAG_CHECK_ENDSTOPS (1 << 2)
#define FLAG_BLOCKED (1 << 3)
#define FLAG_CANCELABLE (1 << 4)
#define FLAG_SYNC (1 << 5)
#define FLAG_SYNC_WAIT (1 << 6)
#define FLAG_USE_PRESSURE_ADVANCE (1 << 7)
#define FLAG_PROBE (1 << 8)

/** Are the step parameter computed */
#define FLAG_JOIN_STEPPARAMS_COMPUTED (1 << 0)
/** The right speed is fixed. Don't check this block or any block to the left. */
#define FLAG_JOIN_END_FIXED (1 << 1)
/** The left speed is fixed. Don't check left block. */
#define FLAG_JOIN_START_FIXED (1 << 2)

#define X_AXIS 0
#define Y_AXIS 1
#define Z_AXIS 2
#define E_AXIS 3
#define H_AXIS 4
#define A_AXIS 5
#define B_AXIS 6
#define C_AXIS 7

#if NUM_AXES != 4
#if NUM_AXES != 5
#if NUM_AXES != 8
#error Invalid number of axis
#endif
#endif
#endif

class Delta;

struct Step
{
    double time;
    unsigned char axis;
    bool direction;

    Step(double time, unsigned char axis, bool direction)
        : time(time)
        , axis(axis)
        , direction(direction)
    {
    }

    bool operator<(Step const& o) const
    {
        return time > o.time;
    }
};

struct StepperPathParameters
{
    double baseSpeed;
    double startSpeed;
    double cruiseSpeed;
    double endSpeed;
    double accel;
    double distance;

    double baseAccelEnd;
    double baseCruiseEnd;
    double baseMoveEnd;

    double moveEnd;

    mutable unsigned int accelSteps;
    mutable unsigned int cruiseSteps;
    mutable unsigned int decelSteps;

    inline void zero()
    {
        startSpeed = 0;
        cruiseSpeed = 0;
        endSpeed = 0;
        accel = 0;
        distance = 0;

        accelSteps = 0;
        cruiseSteps = 0;
        decelSteps = 0;
    }

    double dilateTime(double t) const;

    double finalTime() const;
};

class Path
{
private:
    // These fields change throughout the lifecycle of a Path
    unsigned int joinFlags;
    std::atomic_uint_fast32_t flags;
    double maxJunctionSpeed; /// Max. junction speed between this and next segment

    // These fields are constant after initialization
    double distance; /// Total distance of the move in NUM_AXIS-dimensional space in meters
    unsigned char moveMask;
    unsigned long long timeInTicks; /// Time for completing a move (optimistically assuming it runs full speed the whole time)
    VectorN speeds;
    VectorN worldMove;
    double fullSpeed; /// Cruising speed in m/s
    double startSpeed; /// Starting speed in m/s
    double endSpeed; /// Exit speed in m/s
    double accel; /// Acceleration in m/s^2
    IntVectorN startMachinePos; /// Starting position of the machine

    StepperPathParameters stepperPath;
    std::array<std::vector<Step>, NUM_AXES> steps;

    Path(const Path& path) = delete;
    Path& operator=(const Path&) = delete;

public:
    Path();
    Path(Path&&);

    Path& operator=(Path&&);

    void initialize(const IntVectorN& machineStart,
        const IntVectorN& machineEnd,
        const VectorN& worldStart,
        const VectorN& worldEnd,
        const VectorN& stepsPerM,
        const VectorN& maxSpeeds, /// Maximum allowable speeds in m/s
        const VectorN& maxAccelMPerSquareSecond,
        double requestedSpeed,
        double requestedAccel,
        int axisConfig,
        const Delta& delta,
        bool cancelable,
        bool is_probe);

    double runFinalStepCalculations();

    void zero();

    inline void clearJoinFlags()
    {
        joinFlags = 0;
    }

    inline bool areParameterUpToDate()
    {
        return joinFlags & FLAG_JOIN_STEPPARAMS_COMPUTED;
    }

    inline void invalidateStepperPathParameters()
    {
        joinFlags &= ~FLAG_JOIN_STEPPARAMS_COMPUTED;
        stepperPath.zero();
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

    inline bool isCancelable()
    {
        return flags & FLAG_CANCELABLE;
    }

    inline void setEndSpeedFixed(bool newState)
    {
        joinFlags = (newState ? joinFlags | FLAG_JOIN_END_FIXED : joinFlags & ~FLAG_JOIN_END_FIXED);
    }

    inline void clearFlags()
    {
        flags = 0;
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

    inline bool willMoveReachFullSpeed()
    {
        return flags & FLAG_WILL_REACH_FULL_SPEED;
    }

    inline bool isSyncEvent()
    {
        return flags & FLAG_SYNC;
    }

    inline bool isSyncWaitEvent()
    {
        return flags & FLAG_SYNC_WAIT;
    }

    inline void setSyncEvent(bool wait)
    {
        flags |= wait ? FLAG_SYNC_WAIT : FLAG_SYNC;
    }

    inline bool willUsePressureAdvance()
    {
        return flags & FLAG_USE_PRESSURE_ADVANCE;
    }

    inline bool isProbeMove()
    {
        return flags & FLAG_PROBE;
    }

    inline bool isNoMove()
    {
        return (moveMask & 255) == 0;
    }

    inline bool isAxisMove(unsigned int axis)
    {
        return (moveMask & (1 << axis)) != 0;
    }

    inline bool isAxisOnlyMove(unsigned int axis)
    {
        return (moveMask & 255) == (unsigned int)(1 << axis);
    }

    inline unsigned char getAxisMoveMask()
    {
        return moveMask & 255;
    }

    inline unsigned long long getTimeInTicks()
    {
        return timeInTicks;
    }

    inline void setTimeInTicks(unsigned long time)
    {
        timeInTicks = time;
    }

    inline const VectorN& getSpeeds()
    {
        return speeds;
    }

    inline const VectorN& getWorldMove()
    {
        return worldMove;
    }

    inline double getMaxJunctionSpeed()
    {
        return maxJunctionSpeed;
    }

    inline void setMaxJunctionSpeed(double speed)
    {
        maxJunctionSpeed = speed;
    }

    inline double getStartSpeed()
    {
        return startSpeed;
    }

    inline void setStartSpeed(double speed)
    {
        startSpeed = speed;
        invalidateStepperPathParameters();
    }

    inline double getFullSpeed()
    {
        return fullSpeed;
    }

    inline double getEndSpeed()
    {
        return endSpeed;
    }

    inline void setEndSpeed(double speed)
    {
        endSpeed = speed;
        invalidateStepperPathParameters();
    }

    inline double getAcceleration()
    {
        return accel;
    }

    inline double getDistance()
    {
        return distance;
    }

    /// Note: This magical number is present because it's useful in the formula
    /// v^2 = v0^2 + 2 * a * (r - r0)
    /// This determines final velocity from initial velocity, acceleration, and
    /// distance traveled. It's useful because it doesn't involve time.
    inline double getAccelerationDistance2()
    {
        return 2.0 * distance * accel;
    }

    const IntVectorN& getStartMachinePos()
    {
        return startMachinePos;
    }

    std::array<std::vector<Step>, NUM_AXES>& getSteps()
    {
        return steps;
    }

    void updateStepperPathParameters();
};

#endif /* defined(__PathPlanner__Path__) */
