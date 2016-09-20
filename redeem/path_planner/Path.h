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
#include <atomic>
#include <vector>
#include "config.h"
#include "StepperCommand.h"

#define FLAG_WARMUP 1
#define FLAG_NOMINAL 2
#define FLAG_DECELERATING 4
#define FLAG_ACCELERATION_ENABLED 8
#define FLAG_CHECK_ENDSTOPS 16
#define FLAG_SKIP_ACCELERATING 32
#define FLAG_SKIP_DEACCELERATING 64
#define FLAG_BLOCKED 128
#define FLAG_CANCELABLE 256
#define FLAG_SYNC 512
#define FLAG_SYNC_WAIT 1024
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

class Path {
private:
  unsigned int joinFlags;
  std::atomic_uint_fast32_t flags;

  int primaryAxis;                /// < Axis with longest move. 
  unsigned long long timeInTicks; /// < Time for completing a move. 
  unsigned int dir;               /// < Direction of movement. 1 = X+, 2 = Y+, 4= Z+, values can be combined.
  std::vector<int> delta;         /// < Steps we want to move.
  std::vector<int> error;         /// < Error calculation for Bresenham algorithm
  std::vector<FLOAT_T> speeds;    /// < Speeds for each axis
  std::vector<FLOAT_T> accels;    /// < Acceleration for each axis
  FLOAT_T fullSpeed;              /// < Desired speed m/s
  FLOAT_T invFullSpeed;           /// < 1.0/fullSpeed for fatser computation
  FLOAT_T accelerationDistance2;  /// < Real 2.0*distanceÜacceleration mm²/s²
  FLOAT_T maxJunctionSpeed;       /// < Max. junction speed between this and next segment
  FLOAT_T startSpeed;             /// < Starting speed in m/s
  FLOAT_T endSpeed;               /// < Exit speed in m/s
  FLOAT_T minSpeed;
  FLOAT_T distance;
  unsigned int fullInterval;      /// < interval at full speed in ticks/step.
  unsigned int accelSteps;        /// < How much steps does it take, to reach the plateau.
  unsigned int decelSteps;        /// < How much steps does it take, to reach the end speed.
  unsigned int accelerationPrim;  /// < Acceleration along primary axis in steps/s²
  unsigned int fAcceleration;     /// < accelerationPrim*262144/F_CPU
  FLOAT_T vMax;                   /// < Maximum reached speed in steps/s.
  FLOAT_T vStart;                 /// < Starting speed in steps/s.
  FLOAT_T vEnd;                   /// < End speed in steps/s
  unsigned int stepsRemaining;    /// < Remaining steps, until move is finished

  std::vector<SteppersCommand> commands;


  inline bool areParameterUpToDate() {
    return joinFlags & FLAG_JOIN_STEPPARAMS_COMPUTED;
  }

  inline void invalidateParameter() {
    joinFlags &= ~FLAG_JOIN_STEPPARAMS_COMPUTED;
  }

  inline void setParameterUpToDate() {
    joinFlags |= FLAG_JOIN_STEPPARAMS_COMPUTED;
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

  inline void setCancelable(bool newState) {
    joinFlags = (newState ? joinFlags | FLAG_CANCELABLE : joinFlags & ~FLAG_CANCELABLE);
  }

  inline void setEndSpeedFixed(bool newState) {
    joinFlags = (newState ? joinFlags | FLAG_JOIN_END_FIXED : joinFlags & ~FLAG_JOIN_END_FIXED);
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

  inline bool isNominalMove() {
    return flags & FLAG_NOMINAL;
  }

  inline void setNominalMove() {
    flags |= FLAG_NOMINAL;
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
  inline void setMoveOfAxis(unsigned int axis) {
    dir |= (256 << axis);
  }

  inline bool isAxisMove(unsigned int axis) {
    return (dir & (256 << axis));
  }

  inline void setPositiveDirectionForAxis(unsigned int axis) {
    dir |= (1 << axis);
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

  inline unsigned long getWaitMS() {
    return timeInTicks;
  }

  inline void setWaitMS(unsigned long wait) {
    timeInTicks = wait;
  }

  inline bool moveDecelerating(unsigned int stepNumber) {
    if (stepsRemaining - stepNumber <= decelSteps) {
      if (!(flags & FLAG_DECELERATING)) {
	flags |= FLAG_DECELERATING;
      }
      return true;
    }
    else
      return false;
  }

  inline bool moveAccelerating(unsigned int stepNumber) {
    return stepNumber <= accelSteps;
  }

  void updateStepsParameter();

public:

  FLOAT_T speed; // Feedrate in m/s
  FLOAT_T accel; // Accleeration in m/s^2

  std::vector<FLOAT_T> startPos;
  std::vector<FLOAT_T> endPos;


  Path();
  Path(const Path& path);

  friend class PathPlanner;
};


#endif /* defined(__PathPlanner__Path__) */
