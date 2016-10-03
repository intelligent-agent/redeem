
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

#include <cmath>
#include "Path.h"
#include "Logger.h"

void Path::zero() {
  joinFlags = 0;
  flags = 0;

  primaryAxis = 0;
  timeInTicks = 0;
  dir = 0;

  deltas.assign(NUM_AXES, 0);
  errors.assign(NUM_AXES, 0);
  speeds.assign(NUM_AXES, 0);

  fullSpeed = 0;
  invFullSpeed = 0;
  accelerationDistance2 = 0;
  maxJunctionSpeed = 0;
  startSpeed = 0;
  endSpeed = 0;
  minSpeed = 0;
  distance = 0;
  speed = 0;
  accel = 0;
  fullInterval = 0;
  primaryAxisAcceleration = 0;
  primaryAxisSteps = 0;

  startPos.assign(NUM_AXES, 0);
  endPos.assign(NUM_AXES, 0);

  stepperPath = { 0 };
}

Path::Path() {
  zero();
}

Path::Path(const Path& path) {
  // copy constructor
  joinFlags = path.joinFlags;
  flags = path.flags.load();

  primaryAxis = path.primaryAxis;
  timeInTicks = path.timeInTicks;
  dir = path.dir;

  deltas = path.deltas;
  errors = path.errors;
  speeds = path.speeds;

  fullSpeed = path.fullSpeed;
  invFullSpeed = path.invFullSpeed;
  accelerationDistance2 = path.accelerationDistance2;
  maxJunctionSpeed = path.maxJunctionSpeed;
  startSpeed = path.startSpeed;
  endSpeed = path.endSpeed;
  minSpeed = path.minSpeed;
  distance = path.distance;
  speed = path.speed;
  accel = path.accel;
  fullInterval = path.fullInterval;
  primaryAxisAcceleration = path.primaryAxisAcceleration;
  primaryAxisSteps = path.primaryAxisSteps;

  startPos = path.startPos;
  endPos = path.endPos;

  stepperPath = path.stepperPath;
}

void Path::initialize(const std::vector<FLOAT_T>& startPos,
		      const std::vector<FLOAT_T>& endPos,
		      FLOAT_T distance,
		      FLOAT_T speed,
		      FLOAT_T accel,
		      bool cancelable) {

  LOG("Path: Initialize()"<< std::endl);
  this->zero();

  primaryAxis = X_AXIS;
  this->startPos = startPos;
  this->endPos = endPos;
  this->distance = distance;
  this->speed = speed;
  this->accel = accel;

  for (int axis = 0; axis < NUM_AXES; axis++) {
    deltas[axis] = endPos[axis] - startPos[axis];

    // set bits for axes with positive moves and make delta absolute
    if (deltas[axis] >= 0)
      dir |= (1 << axis);
    else
      deltas[axis] *= -1;

    // set bits for axes that move at all
    if (deltas[axis] != 0) {
      dir |= (256 << axis);
      LOG("Path: Axis " << axis << " is move since p->delta is " << deltas[axis] << std::endl);
    }

    // determine primary axis for the move
    if (deltas[axis] > deltas[primaryAxis])
      primaryAxis = axis;
  }

  LOG("Path: Primary axis is " << primaryAxis << std::endl);

  joinFlags = (cancelable ? FLAG_CANCELABLE : 0);
  flags = 0;
  primaryAxisSteps = deltas[primaryAxis];
  timeInTicks = F_CPU * distance / speed;

  LOG("Path: Distance in m:     " << distance << std::endl);
  LOG("Path: Speed in m/s:      " << speed << std::endl);
  LOG("Path: Accel in m/s^2:    " << accel << std::endl);
  LOG("Path: Ticks :            " << timeInTicks << std::endl);
  LOG("Path: StartSpeed in m/s: " << startSpeed << std::endl);
  LOG("Path: EndSpeed in m/s:   " << endSpeed << std::endl);
}

void Path::calculate(const std::vector<FLOAT_T>& axis_diff,
		     const std::vector<FLOAT_T>& minSpeeds,
		     const std::vector<FLOAT_T>& maxSpeeds,
		     const std::vector<FLOAT_T>& maxAccelStepsPerSquareSecond) {

  std::vector<unsigned int> axisInterval(NUM_AXES, 0);

  LOG( "Path: CalculateMove: Time in ticks:    " << timeInTicks << " ticks" << std::endl);

  // Compute the slowest allowed interval (ticks/step), so maximum feedrate is not violated
  unsigned int limitInterval = (float)timeInTicks / (float)primaryAxisSteps;
  // until not violated by other constraints, this is the target interval
  LOG( "Path: CalculateMove: limitInterval is " << limitInterval << " steps/s" << std::endl);

  for (int i = 0; i < NUM_AXES; i++) {
    if (isAxisMove(i)) {
      axisInterval[i] = fabs(axis_diff[i] * F_CPU) / (maxSpeeds[i] * primaryAxisSteps); // m*ticks/s/(mm/s*steps) = ticks/step
      limitInterval = std::max(axisInterval[i], limitInterval);
    }
    else
      axisInterval[i] = 0;
    //LOG( "Path: CalculateMove: AxisInterval " << i << ": " << axisInterval[i] << std::endl);
    //LOG( "Path: CalculateMove: AxisAccel   " << i << ": " << maxAccelStepsPerSquareSecond[i] << std::endl);
  }

  LOG("Path: CalculateMove: limitInterval is " << limitInterval << " steps/s" << std::endl);
  fullInterval = limitInterval; // This is our target interval

  // this is the time if we move at full speed for the entire move
  FLOAT_T timeAtFullSpeed = (limitInterval * primaryAxisSteps); // ticks/step * steps = ticks

  for (int i = 0; i < NUM_AXES; i++) {
    if (isAxisMove(i)) {
      axisInterval[i] = timeAtFullSpeed / deltas[i];
      speeds[i] = -std::fabs(axis_diff[i] / timeAtFullSpeed); // m/tick
      if (isAxisNegativeMove(i))
	speeds[i] *= -1;
      //p->accels[i] = maxAccelerationMPerSquareSecond[i];
    }
    else
      speeds[i] = 0;
  }

  fullSpeed = (distance / timeAtFullSpeed)*F_CPU;
  invFullSpeed = 1.0 / fullSpeed;

  // slowest time to accelerate from v0 to limitInterval determines used acceleration
  // t = (v_end-v_start)/a
  FLOAT_T slowest_axis_plateau_time_repro = 1e15; // repro to reduce division Unit: 1/s
  for (int i = 0; i < NUM_AXES; i++) {
    if (isAxisMove(i)) {
      // v = a * t => t = v/a = F_CPU/(c*a) => 1/t = c*a/F_CPU
      slowest_axis_plateau_time_repro = std::min(slowest_axis_plateau_time_repro, (FLOAT_T)axisInterval[i] * maxAccelStepsPerSquareSecond[i]); //  steps/s^2 * step/tick  Ticks/s^2
    }
  }

  //LOG("slowest_axis_plateau_time_repro: "<<slowest_axis_plateau_time_repro<<std::endl);
  //LOG("axisInterval[p->primaryAxis]: " << axisInterval[p->primaryAxis] << std::endl);

  // Errors for delta move are initialized in timer (except extruder)
  errors[0] = errors[1] = errors[2] = deltas[primaryAxis] >> 1;
  primaryAxisAcceleration = slowest_axis_plateau_time_repro / axisInterval[primaryAxis]; // a = v/t = F_CPU/(c*t): Steps/s^2

  //Now we can calculate the new primary axis acceleration, so that the slowest axis max acceleration is not violated
  //LOG("p->accelerationPrim: " << p->accelerationPrim << " steps/s²"<< std::endl);


  accelerationDistance2 = 2.0 * distance * slowest_axis_plateau_time_repro * fullSpeed / F_CPU; // m^2/s^2
  startSpeed = endSpeed = minSpeed = calculateSafeSpeed(minSpeeds);
  // Can accelerate to full speed within the line
  if (startSpeed * startSpeed + accelerationDistance2 >= fullSpeed * fullSpeed)
    setMoveWillReachFullSpeed();

  //LOG("fullInterval: " << p->fullInterval << " ticks" << std::endl);
  //LOG("fullSpeed: " << p->fullSpeed << " m/s" << std::endl);

  invalidateStepperPathParameters();
}

FLOAT_T Path::calculateSafeSpeed(const std::vector<FLOAT_T>& minSpeeds) {
  FLOAT_T safe = 1e15;

  // Cap the speed based on axis. 
  // TODO: Add factor?
  for (int i = 0; i<NUM_AXES; i++) {
    if (isAxisMove(i)) {
      safe = std::min(safe, minSpeeds[i]);
    }
  }
  safe = std::min(safe, fullSpeed);
  return safe;
}

/** Update parameter used by updateTrapezoids

Computes the acceleration/decelleration steps and advanced parameter associated.
*/
void Path::updateStepperPathParameters() {
  if (areParameterUpToDate() || isWarmUp())
    return;

  stepperPath.vMax = F_CPU / fullInterval; // maximum steps per second, we can reach   
  //LOG("vMax for path is : " << p->vMax << " steps/s "<< std::endl);	

  LOG( "Path::updateStepperPathParameters()"<<std::endl);
  FLOAT_T startFactor = startSpeed * invFullSpeed;
  FLOAT_T endFactor = endSpeed   * invFullSpeed;
  stepperPath.vStart = stepperPath.vMax * startFactor; //starting speed
  stepperPath.vEnd = stepperPath.vMax * endFactor;
  LOG("Path::vStart is " << stepperPath.vStart << " steps/s" <<std::endl);
  FLOAT_T vmax2 = stepperPath.vMax*stepperPath.vMax;
  stepperPath.accelSteps = (((vmax2 - (stepperPath.vStart * stepperPath.vStart))
    / (primaryAxisAcceleration * 2)) + 1); // Always add 1 for missing precision
  stepperPath.decelSteps = (((vmax2 - (stepperPath.vEnd   * stepperPath.vEnd))
    / (primaryAxisAcceleration * 2)) + 1);

  LOG("Path::accelSteps before cap: " << stepperPath.accelSteps << " steps" <<std::endl);
  if (stepperPath.accelSteps + stepperPath.decelSteps >= primaryAxisSteps) {   // can't reach limit speed
    unsigned int red = (stepperPath.accelSteps + stepperPath.decelSteps + 2 - primaryAxisSteps) >> 1;
    stepperPath.accelSteps = stepperPath.accelSteps - std::min(stepperPath.accelSteps, red);
    stepperPath.decelSteps = stepperPath.decelSteps - std::min(stepperPath.decelSteps, red);

    assert(!willMoveReachFullSpeed());
  }
  LOG("accelSteps: " << stepperPath.accelSteps << " steps" <<std::endl);

  joinFlags |= FLAG_JOIN_STEPPARAMS_COMPUTED;
}
