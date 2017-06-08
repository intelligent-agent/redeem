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

#include <stdint.h>
#include <stddef.h>
#include <assert.h>
#include <atomic>
#include <vector>
#include <string>
#include <array>
#include <vector>
#include "config.h"
#include "StepperCommand.h"
#include "vectorN.h"

#define FLAG_WILL_REACH_FULL_SPEED (1 << 0)
#define FLAG_ACCELERATION_ENABLED  (1 << 1)
#define FLAG_CHECK_ENDSTOPS        (1 << 2)
#define FLAG_BLOCKED               (1 << 3)
#define FLAG_CANCELABLE            (1 << 4)
#define FLAG_SYNC                  (1 << 5)
#define FLAG_SYNC_WAIT             (1 << 6)
#define FLAG_USE_PRESSURE_ADVANCE  (1 << 7)

/** Are the step parameter computed */
#define FLAG_JOIN_STEPPARAMS_COMPUTED (1 << 0)
/** The right speed is fixed. Don't check this block or any block to the left. */
#define FLAG_JOIN_END_FIXED           (1 << 1)
/** The left speed is fixed. Don't check left block. */
#define FLAG_JOIN_START_FIXED         (1 << 2)


#define X_AXIS 0
#define Y_AXIS 1
#define Z_AXIS 2
#define E_AXIS 3
#define H_AXIS 4
#define A_AXIS 5
#define B_AXIS 6
#define C_AXIS 7

#if NUM_AXES!=4
#if NUM_AXES!=5
#if NUM_AXES!=8
#error Invalid number of axis
#endif
#endif
#endif

class Delta;

struct Step {
  FLOAT_T time;
  unsigned char axis;
  bool direction;

  Step(FLOAT_T time, unsigned char axis, bool direction)
    : time(time),
    axis(axis),
    direction(direction)
  {}

  bool operator<(Step const& o) const {
    return time > o.time;
  }
};

struct StepperPathParameters {
  FLOAT_T baseSpeed;
  FLOAT_T startSpeed;
  FLOAT_T cruiseSpeed;
  FLOAT_T endSpeed;
  FLOAT_T accel;
  FLOAT_T distance;

  FLOAT_T baseAccelEnd;
  FLOAT_T baseCruiseEnd;
  FLOAT_T baseMoveEnd;

  FLOAT_T moveEnd;

  mutable unsigned long long accelSteps;
  mutable unsigned long long cruiseSteps;
  mutable unsigned long long decelSteps;

  inline void zero() {
    startSpeed = 0;
    cruiseSpeed = 0;
    endSpeed = 0;
    accel = 0;
    distance = 0;

    accelSteps = 0;
    cruiseSteps = 0;
    decelSteps = 0;
  }

  FLOAT_T dilateTime(FLOAT_T t) const;

  FLOAT_T finalTime() const;
};

class Path {
private:
  // These fields change throughout the lifecycle of a Path
  unsigned int joinFlags;
  std::atomic_uint_fast32_t flags;
  FLOAT_T maxJunctionSpeed;       /// Max. junction speed between this and next segment

  // These fields are constant after initialization
  FLOAT_T distance;               /// Total distance of the move in NUM_AXIS-dimensional space in meters
  unsigned char moveMask;
  unsigned long long timeInTicks; /// Time for completing a move (optimistically assuming it runs full speed the whole time)
  VectorN speeds;
  FLOAT_T fullSpeed;              /// Cruising speed in m/s
  FLOAT_T startSpeed;             /// Starting speed in m/s
  FLOAT_T endSpeed;               /// Exit speed in m/s
  FLOAT_T minSpeed;               /// Minimum allowable speed for the move
  FLOAT_T accel;                  /// Acceleration in m/s^2

  StepperPathParameters stepperPath;
  std::array<std::vector<Step>, NUM_AXES> steps;

  FLOAT_T calculateSafeSpeed(const VectorN& minSpeeds);

public:
  Path();
  Path(const Path& path);
  Path& operator=(const Path&);
  Path& operator=(Path&&);

  void initialize(const IntVectorN& machineStart,
    const IntVectorN& machineEnd,
    const VectorN& worldStart,
    const VectorN& worldEnd,
    const VectorN& stepsPerM,
    const VectorN& minSpeeds, /// Minimum allowable speeds in m/s
    const VectorN& maxSpeeds, /// Maximum allowable speeds in m/s
    const VectorN& maxAccelMPerSquareSecond,
    FLOAT_T requestedSpeed,
    FLOAT_T requestedAccel,
    int axisConfig,
    const Delta& delta,
    bool cancelable);

  FLOAT_T runFinalStepCalculations();

  void zero();

  inline void clearJoinFlags() {
    joinFlags = 0;
  }

  inline bool areParameterUpToDate() {
    return joinFlags & FLAG_JOIN_STEPPARAMS_COMPUTED;
  }

  inline void invalidateStepperPathParameters() {
    joinFlags &= ~FLAG_JOIN_STEPPARAMS_COMPUTED;
    stepperPath.zero();
  }

  inline bool isStartSpeedFixed() {
    return joinFlags & FLAG_JOIN_START_FIXED;
  }

  inline void setStartSpeedFixed(bool newState) {
    joinFlags = (newState ? joinFlags | FLAG_JOIN_START_FIXED : joinFlags & ~FLAG_JOIN_START_FIXED);
  }

  inline void fixStartAndEndSpeed() {
    joinFlags |= FLAG_JOIN_END_FIXED | FLAG_JOIN_START_FIXED;
  }

  inline bool isEndSpeedFixed() {
    return joinFlags & FLAG_JOIN_END_FIXED;
  }

  inline bool isCancelable() {
    return flags & FLAG_CANCELABLE;
  }

  inline void setEndSpeedFixed(bool newState) {
    joinFlags = (newState ? joinFlags | FLAG_JOIN_END_FIXED : joinFlags & ~FLAG_JOIN_END_FIXED);
  }

  inline void clearFlags() {
    flags = 0;
  }

  inline void block() {
    flags |= FLAG_BLOCKED;
  }

  inline void unblock() {
    flags &= ~FLAG_BLOCKED;
  }

  inline bool isBlocked() {
    return flags & FLAG_BLOCKED;
  }

  inline bool isCheckEndstops() {
    return flags & FLAG_CHECK_ENDSTOPS;
  }

  inline bool willMoveReachFullSpeed() {
    return flags & FLAG_WILL_REACH_FULL_SPEED;
  }

  inline bool isSyncEvent() {
    return flags & FLAG_SYNC;
  }

  inline bool isSyncWaitEvent() {
    return flags & FLAG_SYNC_WAIT;
  }

  inline void setSyncEvent(bool wait) {
    flags |= wait ? FLAG_SYNC_WAIT : FLAG_SYNC;
  }

  inline bool willUsePressureAdvance() {
    return flags & FLAG_USE_PRESSURE_ADVANCE;
  }

  inline bool isNoMove() {
    return (moveMask & 255) == 0;
  }

  inline bool isAxisMove(unsigned int axis) {
    return (moveMask & (1 << axis)) != 0;
  }

  inline bool isAxisOnlyMove(unsigned int axis) {
    return (moveMask & 255) == (unsigned int)(1 << axis);
  }

  inline unsigned char getAxisMoveMask() {
    return moveMask & 255;
  }

  inline unsigned long getTimeInTicks() {
    return timeInTicks;
  }

  inline void setTimeInTicks(unsigned long time) {
    timeInTicks = time;
  }

  inline const VectorN& getSpeeds() {
    return speeds;
  }

  inline FLOAT_T getMaxJunctionSpeed() {
    return maxJunctionSpeed;
  }

  inline void setMaxJunctionSpeed(FLOAT_T speed) {
    maxJunctionSpeed = speed;
  }

  inline FLOAT_T getStartSpeed() {
    return startSpeed;
  }

  inline void setStartSpeed(FLOAT_T speed) {
    startSpeed = speed;
    invalidateStepperPathParameters();
  }

  inline FLOAT_T getFullSpeed() {
    return fullSpeed;
  }

  inline FLOAT_T getEndSpeed() {
    return endSpeed;
  }

  inline void setEndSpeed(FLOAT_T speed) {
    endSpeed = speed;
    invalidateStepperPathParameters();
  }

  inline FLOAT_T getMinSpeed() {
    return minSpeed;
  }

  inline FLOAT_T getAcceleration() {
    return accel;
  }

  /// Note: This magical number is present because it's useful in the formula
  /// v^2 = v0^2 + 2 * a * (r - r0)
  /// This determines final velocity from initial velocity, acceleration, and
  /// distance traveled. It's useful because it doesn't involve time.
  inline FLOAT_T getAccelerationDistance2() {
    return 2.0 * distance * accel;
  }

  std::array<std::vector<Step>, NUM_AXES>& getSteps() {
    return steps;
  }

  void updateStepperPathParameters();
};


#endif /* defined(__PathPlanner__Path__) */
