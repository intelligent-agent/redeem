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
#include "config.h"
#include "StepperCommand.h"

#define FLAG_WARMUP                (1 << 0)
#define FLAG_WILL_REACH_FULL_SPEED (1 << 1)
#define FLAG_ACCELERATION_ENABLED  (1 << 2)
#define FLAG_CHECK_ENDSTOPS        (1 << 3)
#define FLAG_BLOCKED               (1 << 4)
#define FLAG_CANCELABLE            (1 << 5)
#define FLAG_SYNC                  (1 << 6)
#define FLAG_SYNC_WAIT             (1 << 7)

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

struct StepperPathParameters {
  FLOAT_T vMax;                   /// Maximum reached speed in steps/s.
  FLOAT_T vStart;                 /// Starting speed in steps/s.
  FLOAT_T vEnd;                   /// End speed in steps/s

  unsigned int accelSteps;        /// How many steps does it take to reach the plateau.
  unsigned int decelSteps;        /// How many steps does it take to reach the end speed.
};

class Path {
private:
  unsigned int joinFlags;
  std::atomic_uint_fast32_t flags;

  int primaryAxis;                /// Axis with longest move.
  unsigned long long timeInTicks; /// Time for completing a move.
  unsigned int dir;               /// Direction of movement (1 = X+, 2 = Y+, 4= Z+) and whether an axis moves at all (256 = X+, 512 = Y+, 1024 = Z+)
  std::vector<int> deltas;         /// Steps we want to move (absolute)
  std::vector<int> errors;         /// Error calculation for Bresenham algorithm
  std::vector<FLOAT_T> speeds;    /// Speeds for each axis in m/tick
  FLOAT_T fullSpeed;              /// Desired speed m/s
  FLOAT_T invFullSpeed;           /// 1.0/fullSpeed for fatser computation
  FLOAT_T accelerationDistance2;  /// Real 2.0*distanceÜacceleration mm²/s²
  FLOAT_T maxJunctionSpeed;       /// Max. junction speed between this and next segment
  FLOAT_T startSpeed;             /// Starting speed in m/s
  FLOAT_T endSpeed;               /// Exit speed in m/s
  FLOAT_T minSpeed;
  FLOAT_T distance;
  FLOAT_T speed; // Feedrate in m/s
  FLOAT_T accel; // Acceleration in m/s^2
  unsigned int fullInterval;      /// interval at full speed in ticks/step.
  unsigned int primaryAxisAcceleration;  /// Acceleration along primary axis in steps/s²
  unsigned int primaryAxisSteps;  /// Total number of primary axis steps in the move

  std::vector<FLOAT_T> startPos;
  std::vector<FLOAT_T> endPos;



  StepperPathParameters stepperPath;

  void zero();
  FLOAT_T calculateSafeSpeed(const std::vector<FLOAT_T>& minSpeeds);

public:
  Path();
  Path(const Path& path);

  void initialize(const std::vector<FLOAT_T>& start,
		  const std::vector<FLOAT_T>& end,
		  FLOAT_T distance,
		  FLOAT_T speed,
		  FLOAT_T accel,
		  bool cancelable);

  void calculate(const std::vector<FLOAT_T>& axis_diff,
		 const std::vector<FLOAT_T>& minSpeeds,
		 const std::vector<FLOAT_T>& maxSpeeds,
		 const std::vector<FLOAT_T>& maxAccelStepsPerSquareSecond);

  inline void clearJoinFlags() {
    joinFlags = 0;
  }

  inline bool areParameterUpToDate() {
    return joinFlags & FLAG_JOIN_STEPPARAMS_COMPUTED;
  }

  inline void invalidateStepperPathParameters() {
    joinFlags &= ~FLAG_JOIN_STEPPARAMS_COMPUTED;
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
    return joinFlags & FLAG_CANCELABLE;
  }

  inline void setEndSpeedFixed(bool newState) {
    joinFlags = (newState ? joinFlags | FLAG_JOIN_END_FIXED : joinFlags & ~FLAG_JOIN_END_FIXED);
  }

  inline void clearFlags() {
    flags = 0;
  }

  inline bool isWarmUp() {
    return flags & FLAG_WARMUP;
  }

  inline uint8_t getWaitForXLinesFilled() {
    return primaryAxis;
  }

  inline void setWaitForXLinesFilled(uint8_t b) {
    primaryAxis = b;
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

  inline void setMoveWillReachFullSpeed() {
    flags |= FLAG_WILL_REACH_FULL_SPEED;
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

  inline bool isNoMove() {
    return (dir & (255 << 8)) == 0;
  }

  inline bool isAxisMove(unsigned int axis) {
    return (dir & (256 << axis));
  }

  inline bool isAxisNegativeMove(unsigned int axis) {
    return (dir & ((256 << axis) + (1 << axis))) == (unsigned int)(256 << axis);
  }

  inline bool isAxisPositiveMove(unsigned int axis) {
    return (dir & ((256 << axis) + (1 << axis))) == (unsigned int)((256 << axis) + (1 << axis));
  }

  inline bool isAxisOnlyMove(unsigned int axis) {
    return ((dir & (255 << 8)) == (unsigned int)(256 << axis));
  }

  inline unsigned long getTimeInTicks() {
    return timeInTicks;
  }

  inline void setTimeInTicks(unsigned long time) {
    timeInTicks = time;
  }

  inline const std::vector<FLOAT_T>& getSpeeds() {
    return speeds;
  }

  inline const std::vector<int>& getDeltas() {
    return deltas;
  }

  inline const std::vector<int>& getInitialErrors() {
    return errors;
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

  inline FLOAT_T getAccelerationDistance2() {
    return accelerationDistance2;
  }

  inline unsigned int getFullInterval() {
    return fullInterval;
  }

  inline int getPrimaryAxis() {
    return primaryAxis;
  }

  inline unsigned int getPrimaryAxisSteps() {
    return primaryAxisSteps;
  }

  inline unsigned int getPrimaryAxisAcceleration() {
    return primaryAxisAcceleration;
  }

  StepperPathParameters getStepperPathParameters() {
    assert(areParameterUpToDate());
    return stepperPath;
  }

  void updateStepperPathParameters();
};


#endif /* defined(__PathPlanner__Path__) */
