
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
#include <algorithm>
#include <numeric>
#include "Path.h"
#include "Delta.h"
#include "Logger.h"

void calculateLinearMove(const int axis, const long long startStep, const long long endStep, const FLOAT_T time, std::priority_queue<Step>& steps)
{
  const FLOAT_T distance = endStep - startStep;

  const bool direction = startStep < endStep;
  const long long stepIncrement = direction ? 1 : -1;
  const FLOAT_T stepOffset = stepIncrement / 2.0;

  long long step = startStep;

  while (step != endStep)
  {
    const FLOAT_T position = step + stepOffset;
    const FLOAT_T stepTime = (position - startStep) / distance * time;

    assert(stepTime > 0 && stepTime < time);

    steps.emplace(Step(stepTime, axis, direction));

    step += stepIncrement;
  }
}

void calculateXYMove(const IntVector3& start, const IntVector3& end, const Vector3& stepsPerM, FLOAT_T time, std::priority_queue<Step>& steps)
{
  for (int i = 0; i < NUM_MOVING_AXES; i++)
  {
    calculateLinearMove(i, start[i], end[i], time, steps);
  }
}

void calculateExtruderMove(const IntVectorN& start, const IntVectorN& end, FLOAT_T time, std::priority_queue<Step>& steps)
{
  for (int i = NUM_MOVING_AXES; i < NUM_AXES; i++)
  {
    calculateLinearMove(i, start[i], end[i], time, steps);
  }
}

void Path::zero() {
  joinFlags = 0;
  flags = 0;

  distance = 0;
  baseSpeed = 0;
  moveMask = 0;

  timeInTicks = 0;
  speeds.zero();
  fullSpeed = 0;
  maxJunctionSpeed = 0;
  startSpeed = 0;
  endSpeed = 0;
  minSpeed = 0;
  accel = 0;

  stepperPath.zero();
  steps = std::priority_queue<Step>();

  assert(steps.size() == 0);
}

Path::Path() {
  zero();
}

Path::Path(const Path& path) {
  operator=(path);
}

Path& Path::operator=(const Path& path) {
  // assignment operator
  joinFlags = path.joinFlags;
  flags = path.flags.load();

  distance = path.distance;
  baseSpeed = path.baseSpeed;
  moveMask = path.moveMask;

  timeInTicks = path.timeInTicks;
  speeds = path.speeds;
  fullSpeed = path.fullSpeed;
  maxJunctionSpeed = path.maxJunctionSpeed;
  startSpeed = path.startSpeed;
  endSpeed = path.endSpeed;
  minSpeed = path.minSpeed;
  accel = path.accel;

  stepperPath = path.stepperPath;
  steps = path.steps;

  return *this;
}

Path& Path::operator=(Path&& path) {
  // move assignment operator
  joinFlags = path.joinFlags;
  flags = path.flags.load();

  distance = path.distance;
  baseSpeed = path.baseSpeed;
  moveMask = path.moveMask;

  timeInTicks = path.timeInTicks;
  speeds = path.speeds;
  fullSpeed = path.fullSpeed;
  maxJunctionSpeed = path.maxJunctionSpeed;
  startSpeed = path.startSpeed;
  endSpeed = path.endSpeed;
  minSpeed = path.minSpeed;
  accel = path.accel;

  stepperPath = path.stepperPath;
  steps = std::move(path.steps);

  return *this;
}

void Path::initialize(const IntVectorN& start,
		      const IntVectorN& end,
		      const VectorN& stepsPerM,
		      FLOAT_T speed,
		      int axisConfig,
		      const Delta& delta,
		      bool cancelable) {
  this->zero();

  const FLOAT_T distance = vabs((end.toVectorN() - start.toVectorN()) / stepsPerM);
  const FLOAT_T time = distance / speed; // m / (m/s) = m * (s/m) = s

  assert(!std::isnan(distance));
  assert(!std::isnan(time));

  this->distance = distance;
  this->baseSpeed = speed;

  LOG("ideal move should be " << speed << " m/s and cover " << distance << " m in " << time << " seconds" << std::endl);

  switch (axisConfig)
  {
  case AXIS_CONFIG_DELTA:
    delta.calculateMove(start.toIntVector3(), end.toIntVector3(), stepsPerM.toVector3(), time, steps);
    break;
  case AXIS_CONFIG_XY:
  case AXIS_CONFIG_H_BELT:
  case AXIS_CONFIG_CORE_XY:
    calculateXYMove(start.toIntVector3(), end.toIntVector3(), stepsPerM.toVector3(), time, steps);
    break;
  default:
    assert(0);
  }

  calculateExtruderMove(start, end, time, steps);

  assert(!steps.empty());

  const IntVectorN move = end - start;

  for (int axis = 0; axis < NUM_AXES; axis++) {
    if (move[axis] != 0)
    {
      moveMask |= (1 << axis);
    }
  }

  joinFlags = 0;
  flags = (cancelable ? FLAG_CANCELABLE : 0);

  assert(!(isAxisMove(E_AXIS) && isAxisMove(H_AXIS))); // both extruders should never move at the same time

  if ((isAxisMove(E_AXIS) && !isAxisOnlyMove(E_AXIS)) || (isAxisMove(H_AXIS) && !isAxisOnlyMove(H_AXIS))) {
    flags |= FLAG_USE_PRESSURE_ADVANCE;
  }

  LOG("Distance in m:     " << distance << std::endl);

  //LOG("StartSpeed in m/s: " << p->startSpeed << std::endl);
  //LOG("EndSpeed in m/s:   " << p->endSpeed << std::endl);
}

void Path::calculate(const VectorN& axis_diff, /// Axis movements expressed in meters
		     const VectorN& minSpeeds, /// Minimum allowable speeds in m/s
		     const VectorN& maxSpeeds, /// Maximum allowable speeds in m/s
		     const VectorN& maxAccelMPerSquareSecond,
		     FLOAT_T requestedSpeed,
		     FLOAT_T requestedAccel) {
  // First we need to figure out the minimum time for the move.
  // We determine this by calculating how long each axis would take to complete its move
  // at its maximum speed.
  FLOAT_T minimumTimeForMove = 0;

  for (int i = 0; i < NUM_AXES; i++) {
    if (isAxisMove(i)) {
      FLOAT_T minimumAxisTimeForMove = fabs(axis_diff[i]) / maxSpeeds[i]; // m / (m/s) = s
      minimumTimeForMove = std::max(minimumTimeForMove, minimumAxisTimeForMove);
    }
  }

  FLOAT_T maximumSpeed = distance / minimumTimeForMove;

  // Now figure out if we can honor the user's requested speed.
  if (requestedSpeed > maximumSpeed) {
    fullSpeed = maximumSpeed;
  }
  else {
    fullSpeed = requestedSpeed;
  }

  assert(!std::isnan(fullSpeed));

  FLOAT_T idealTimeForMove = distance / fullSpeed; // m / (m/s) = s
  timeInTicks = F_CPU * idealTimeForMove; // ticks / s * s = ticks

  // Now determine the maximum possible acceleration to get to fullSpeed.
  FLOAT_T minimumAccelerationTime = 0;
  for (int i = 0; i < NUM_AXES; i++) {
    if (isAxisMove(i)) {
      speeds[i] = axis_diff[i] / idealTimeForMove;
      // v = a * t  =>  t = v / a
      // (steps / second) / (steps / second^2) = seconds
      FLOAT_T minimumAxisAccelerationTime = speeds[i] / maxAccelMPerSquareSecond[i];
      minimumAccelerationTime = std::max(minimumAccelerationTime, minimumAxisAccelerationTime);
    }
    else {
      speeds[i] = 0;
    }
  }

  FLOAT_T maximumAccel = fullSpeed / minimumAccelerationTime;

  accel = std::min(requestedAccel, maximumAccel);
  FLOAT_T idealTimeForAcceleration = fullSpeed / accel; // (m/s) / (m/s^2) = s

  // Calculate whether we're guaranteed to reach cruising speed.
  FLOAT_T maximumAccelDistance = idealTimeForAcceleration * (fullSpeed / 2.0);
  if (2.0 * maximumAccelDistance < distance) {
    // This move has enough distance that we can accelerate from 0 to fullSpeed and back to 0.
    // We'll definitely hit cruising speed.
    flags |= FLAG_WILL_REACH_FULL_SPEED;
  }

  startSpeed = endSpeed = minSpeed = calculateSafeSpeed(minSpeeds);

  LOG("Speed in m/s:      " << fullSpeed << std::endl);
  LOG("Accel in m/s²:     " << accel << std::endl);
  LOG("Ticks :            " << timeInTicks << std::endl);

  invalidateStepperPathParameters();
}

FLOAT_T Path::calculateSafeSpeed(const VectorN& minSpeeds) {
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
  if (areParameterUpToDate())
    return;

  FLOAT_T cruiseSpeed = fullSpeed;

  FLOAT_T accelTime = (fullSpeed - startSpeed) / accel;
  FLOAT_T decelTime = (fullSpeed - endSpeed) / accel;

  FLOAT_T accelDistance = (cruiseSpeed * cruiseSpeed - startSpeed * startSpeed) / (2.0 * accel);
  FLOAT_T decelDistance = (cruiseSpeed * cruiseSpeed - endSpeed * endSpeed) / (2.0 * accel);
  assert(accelDistance >= 0);
  assert(decelDistance >= 0);

  FLOAT_T cruiseDistance = distance - accelDistance - decelDistance;
  FLOAT_T cruiseTime = cruiseDistance / cruiseSpeed;
  
  if (accelDistance + decelDistance > distance) {
    //           cruiseSpeed                  // (no, C++, this isn't a multiline comment)
    //               /\                       //
    //              /  \                      //
    //             /    \ endSpeed            //
    //            /   ---d2                   //
    //startSpeed /                            //
    //           -----d1                      //
    //
    // vf^2 = vi^2 + 2*a*d
    // -> d = (vf^2 - vi^2) / (2*a)
    // distance = d1 + d2
    // -> distance = (cruiseSpeed^2 - startSpeed^2) / (2*accel) + (endSpeed^2 - cruiseSpeed^2) / (2*-accel) // note the negative accel
    // -> distance = (cruiseSpeed^2 - startSpeed^2) / (2*accel) - (endSpeed^2 - cruiseSpeed^2) / (2*accel)
    // -> distance = (cruiseSpeed^2 - startSpeed^2 - endSpeed^2 + cruiseSpeed^2) / (2*accel)
    // -> 2*accel*distance = 2*cruiseSpeed^2 - startSpeed^2 - endSpeed^2
    // -> 2*accel*distance + startSpeed^2 + endSpeed^2 = 2*cruiseSpeed^2
    // -> cruiseSpeed = sqrt(accel*distance + (startSpeed^2 + endSpeed^2) / 2)
    cruiseSpeed = std::sqrt(accel * distance + (startSpeed * startSpeed + endSpeed * endSpeed) / 2.0);

    // Try to reduce cruiseSpeed 1% so we get just a bit of cruising time. This makes the calculations
    // below more stable.
    cruiseSpeed = std::max(startSpeed, std::max(endSpeed, cruiseSpeed * 0.99));

    accelTime = (cruiseSpeed - startSpeed) / accel;
    decelTime = (cruiseSpeed - endSpeed) / accel;

    accelDistance = (cruiseSpeed * cruiseSpeed - startSpeed * startSpeed) / (2.0 * accel);
    decelDistance = (cruiseSpeed * cruiseSpeed - endSpeed * endSpeed) / (2.0 * accel);

    cruiseDistance = distance - accelDistance - decelDistance;

    if (cruiseDistance < 0) {
      // As it turns out, the optimizer can over-accelerate on very short moves because it
      // doesn't check that the end speed of a move is reachable from the start speed within
      // limits. This hasn't been a problem because it only affects moves that are only a few
      // steps in the first place. However, when it occurs, this assert will fire.
      //assert(std::abs(cruiseDistance) < NEGLIGIBLE_ERROR);

      if (accelDistance == 0) {
	assert(accelTime == 0);

	cruiseDistance = 0;
	cruiseTime = 0;
	cruiseSpeed = startSpeed;

	decelDistance = distance;
	decelTime = distance / ((cruiseSpeed + endSpeed) / 2.0);
      }
      else if (decelDistance == 0) {
	assert(decelTime == 0);

	cruiseDistance = 0;
	cruiseTime = 0;
	cruiseSpeed = endSpeed;

	accelDistance = distance;
	accelTime = distance / ((cruiseSpeed + startSpeed) / 2.0);
      }
      else {
	assert(0);
      }
    }

    cruiseTime = cruiseDistance / cruiseSpeed;

    LOG("Move will not reach full speed" << std::endl);
  }

  LOG("accelTime: " << accelTime << " cruiseTime: " << cruiseTime << " decelTime: " << decelTime << std::endl);
  assert(accelTime >= 0 && cruiseTime >= 0 && decelTime >= 0);
  assert(accelDistance >= 0 && cruiseDistance >= 0 && decelDistance >= 0);
  assert(std::abs(distance - (accelDistance + cruiseDistance + decelDistance)) < NEGLIGIBLE_ERROR);

  stepperPath.baseSpeed = baseSpeed;
  stepperPath.startSpeed = startSpeed;
  stepperPath.cruiseSpeed = cruiseSpeed;
  stepperPath.endSpeed = endSpeed;
  stepperPath.accel = accel;
  stepperPath.distance = distance;

  const FLOAT_T& Vi = startSpeed;
  const FLOAT_T& Vc = cruiseSpeed;
  const FLOAT_T& Vf = endSpeed;
  const FLOAT_T& A = accel;
  const FLOAT_T& D = distance;

  const FLOAT_T Vi2 = Vi * Vi;
  const FLOAT_T Vc2 = Vc * Vc;
  const FLOAT_T Vf2 = Vf * Vf;

  stepperPath.baseAccelEnd = (-(Vi2 - Vc2)) / (2 * A*Vc);
  stepperPath.baseCruiseEnd = (Vf2 - Vc2 + 2 * A*D) / (2 * A*Vc);
  stepperPath.baseMoveEnd = D / Vc;

  stepperPath.moveEnd = (Vi2 - 2 * Vc*Vi + Vf2 - 2 * Vc*Vf + 2 * Vc2 + 2 * A*D) / (2 * A*Vc);

  joinFlags |= FLAG_JOIN_STEPPARAMS_COMPUTED;

  assert(areParameterUpToDate());
}

FLOAT_T StepperPathParameters::dilateTime(FLOAT_T t) const
{
  const FLOAT_T& Vi = startSpeed;
  const FLOAT_T& Vc = cruiseSpeed;
  const FLOAT_T& Vf = endSpeed;
  const FLOAT_T& A = accel;
  const FLOAT_T& D = distance;

  const FLOAT_T Vi2 = Vi * Vi;
  const FLOAT_T Vc2 = Vc * Vc;
  const FLOAT_T Vf2 = Vf * Vf;

  assert(t >= 0);

  t *= baseSpeed / cruiseSpeed;

  FLOAT_T result = NAN;

  if (t < baseAccelEnd)
  {
    accelSteps++;
    result = (sqrt(2 * A*Vc*t + Vi2) - Vi) / A;
  }
  else if (t < baseCruiseEnd)
  {
    cruiseSteps++;
    result = (2 * A*Vc*t + Vi2 + (-2)*Vc*Vi + Vc2) / (2 * A*Vc);
  }
  else if (t < baseMoveEnd)
  {
    decelSteps++;
    result = (-(2 * Vc*sqrt((-2)*A*Vc*t + Vf2 + 2 * A*D) - Vi2 + 2 * Vc*Vi - Vf2 + (-2)*Vc2 + (-2)*A*D)) / (2 * A*Vc);
  }
  else
  {
    assert(0);
  }

  assert(!std::isnan(result));

  return result;
}

FLOAT_T StepperPathParameters::finalTime() const
{
  return moveEnd;
}
