
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
#include "Logger.h"

void Path::zero() {
  joinFlags = 0;
  flags = 0;

  distance = 0;
  dir = 0;
  deltas.assign(NUM_AXES, 0);

  timeInTicks = 0;
  speeds.zero();
  accels.zero();
  fullSpeed = 0;
  maxJunctionSpeed = 0;
  startSpeed = 0;
  endSpeed = 0;
  minSpeed = 0;
  accel = 0;

  stepperPath.zero();
}

Path::Path() {
  zero();
}

Path::Path(const Path& path) {
  operator=(path);
}

Path& Path::operator=(const Path& path) {
  // copy constructor
  joinFlags = path.joinFlags;
  flags = path.flags.load();

  distance = path.distance;
  dir = path.dir;
  deltas = path.deltas;

  timeInTicks = path.timeInTicks;
  speeds = path.speeds;
  accels = path.accels;
  fullSpeed = path.fullSpeed;
  maxJunctionSpeed = path.maxJunctionSpeed;
  startSpeed = path.startSpeed;
  endSpeed = path.endSpeed;
  minSpeed = path.minSpeed;
  accel = path.accel;

  stepperPath = path.stepperPath;

  return *this;
}

void Path::initialize(const VectorN& startPos,
		      const VectorN& endPos,
		      FLOAT_T distance,
		      bool cancelable) {
  this->zero();

  assert(!std::isnan(distance));
  this->distance = distance;

  for (int axis = 0; axis < NUM_AXES; axis++) {
    deltas[axis] = endPos[axis] - startPos[axis];

    assert(!std::isnan(deltas[axis]));

    // set bits for axes with positive moves and make delta absolute
    if (deltas[axis] >= 0)
      dir |= (1 << axis);
    else
      deltas[axis] *= -1;

    // set bits for axes that move at all
    if (deltas[axis] != 0) {
      dir |= (256 << axis);
      LOG("Axis " << axis << " is move since p->delta is " << deltas[axis] << std::endl);
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
		     const VectorN& maxAccelStepsPerSquareSecond,
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

  for (int i = 0; i < NUM_AXES; i++) {
    if (isAxisMove(i)) {
      speeds[i] = (FLOAT_T)deltas[i] / idealTimeForMove;
      assert(!std::isnan(speeds[i]));
    }
    else {
      speeds[i] = 0;
    }
  }

  // Now determine the maximum possible acceleration to get to fullSpeed.
  FLOAT_T minimumAccelerationTime = 0;
  for (int i = 0; i < NUM_AXES; i++) {
    if (isAxisMove(i)) {
      // v = a * t  =>  t = v / a
      // (steps / second) / (steps / second^2) = seconds
      FLOAT_T minimumAxisAccelerationTime = speeds[i] / maxAccelStepsPerSquareSecond[i];
      minimumAccelerationTime = std::max(minimumAccelerationTime, minimumAxisAccelerationTime);
    }
  }

  FLOAT_T maximumAccel = fullSpeed / minimumAccelerationTime;

  accel = std::min(requestedAccel, maximumAccel);
  FLOAT_T idealTimeForAcceleration = fullSpeed / accel; // (m/s) / (m/s^2) = s

  for (int i = 0; i < NUM_AXES; i++) {
    if (isAxisMove(i)) {
      accels[i] = speeds[i] / idealTimeForAcceleration;
      assert(!std::isnan(accels[i]));
    }
    else {
      accels[i] = 0;
    }
  }

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

	decelDistance = distance;
	decelTime = distance / ((cruiseSpeed + endSpeed) / 2.0);
      }
      else if (decelDistance == 0) {
	assert(decelTime == 0);

	cruiseDistance = 0;
	cruiseTime = 0;

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

  FLOAT_T startFactor = startSpeed / fullSpeed;
  FLOAT_T endFactor = endSpeed / fullSpeed;

  for (int i = 0; i < NUM_AXES; i++) {
    FLOAT_T dirFactor = isAxisPositiveMove(i) ? 1.0 : -1.0;
    stepperPath.accelStartSpeeds[i] = dirFactor * startFactor * speeds[i];
    stepperPath.accelDeltas[i] = dirFactor * (accelDistance / distance) * deltas[i];
    stepperPath.cruiseDeltas[i] = dirFactor * (cruiseDistance / distance) * deltas[i];
    stepperPath.decelEndSpeeds[i] = dirFactor * endFactor * speeds[i];
    stepperPath.decelDeltas[i] = dirFactor * (decelDistance / distance) * deltas[i];

    assert(std::abs(stepperPath.accelDeltas[i] + stepperPath.cruiseDeltas[i] + stepperPath.decelDeltas[i] - dirFactor * deltas[i]) < CPU_CYCLE_LENGTH);
    assert((deltas[i] != 0) == isAxisMove(i));
    
    FLOAT_T absoluteSteps = calculateStepsForMixedPath(stepperPath.accelStartSpeeds[i], 2.0 * stepperPath.accelDeltas[i] / stepperPath.accelTime - stepperPath.accelStartSpeeds[i], stepperPath.accelTime)
      + calculateStepsForMixedPath(stepperPath.cruiseDeltas[i] / stepperPath.cruiseTime, stepperPath.cruiseDeltas[i] / stepperPath.cruiseTime, stepperPath.cruiseTime)
      + calculateStepsForMixedPath(2.0 * stepperPath.decelDeltas[i] / stepperPath.decelTime - stepperPath.decelEndSpeeds[i], stepperPath.decelEndSpeeds[i], stepperPath.decelTime);

    // Each axis must have an integer number of steps in this path or they won't finish at the same time.
    // It's okay for individual path phases to have non-integer step counts as long as they sum up to an integer.
    assert(std::abs(absoluteSteps - std::lround(absoluteSteps)) < NEGLIGIBLE_ERROR);
  }

  stepperPath.accelTime = accelTime;
  stepperPath.cruiseTime = cruiseTime;
  stepperPath.decelTime = decelTime;

  joinFlags |= FLAG_JOIN_STEPPARAMS_COMPUTED;
}

FLOAT_T Path::calculateStepsForMixedPath(FLOAT_T startSpeed, FLOAT_T endSpeed, FLOAT_T time) {
  if (time == 0 || (startSpeed == 0 && endSpeed == 0)) {
    return 0;
  }

  if (std::signbit(startSpeed) == std::signbit(endSpeed) || startSpeed == 0 || endSpeed == 0) {
    return std::abs(time * (startSpeed + endSpeed) / 2.0);
  }
  else {
    FLOAT_T delta = std::abs(startSpeed) + std::abs(endSpeed);
    return calculateStepsForMixedPath(startSpeed, 0, std::abs(startSpeed) / delta * time)
	 + calculateStepsForMixedPath(0, endSpeed, std::abs(endSpeed) / delta * time);
  }
}

StepperPath::StepperPath() {
}

StepperPath::StepperPath(const StepperPathParameters& params, int axis) {
  calculatePhaseFromStartSpeed(params.accelStartSpeeds[axis], params.accelDeltas[axis], params.accelTime);
  calculateCruisePhase(params.cruiseDeltas[axis], params.cruiseTime);
  calculatePhaseFromEndSpeed(params.decelEndSpeeds[axis], params.decelDeltas[axis], params.decelTime);

  // Run sanity checks
  FLOAT_T calculatedSteps = 0;
  FLOAT_T calculatedTime = 0;
  FLOAT_T absoluteSteps = 0;
  for (PathPhase& phase : phases) {
    calculatedSteps += (phase.direction == StepDirection::Forward ? 1.0 : -1.0) * phase.numSteps;
    calculatedTime += phase.time;
    absoluteSteps += phase.numSteps;
  }

  numSteps = std::lround(absoluteSteps);
  assert(std::abs(numSteps - absoluteSteps) < NEGLIGIBLE_ERROR);

  // add a one-step final phase at the end speed - we don't actually take the final step, but
  // the path planner uses it to determine the end time for the move.
  PathPhase finalPhase = {};
  finalPhase.constant = true;
  finalPhase.rampDir = true;
  finalPhase.direction = StepDirection::None;
  finalPhase.initialDelay = 0;
  finalPhase.numSteps = 1.0;
  finalPhase.startSpeed = finalPhase.endSpeed = 0.0;
  finalPhase.time = 1.0;

  phases.push_back(finalPhase);

  assert(std::abs(calculatedTime - (params.accelTime + params.cruiseTime + params.decelTime)) < CPU_CYCLE_LENGTH);
  assert(phases.size() < INT32_MAX);
}

void StepperPath::calculatePhaseFromStartSpeed(FLOAT_T startSpeed, FLOAT_T distance, FLOAT_T time) {
  if (distance == 0 || time == 0) {
    return;
  }

  assert(std::signbit(startSpeed) == std::signbit(distance) || startSpeed == 0);

  const FLOAT_T endSpeed = 2.0 * distance / time - startSpeed;
  const FLOAT_T accel = 2.0 * (distance - startSpeed * time) / (time * time);

  assert(std::signbit(startSpeed) == std::signbit(endSpeed) || startSpeed == 0 || endSpeed == 0);
  assert(std::abs(endSpeed) > std::abs(startSpeed));
  assert(std::signbit(accel) == std::signbit(startSpeed) || startSpeed == 0);

  calculatePhase(PrimarySpeed::Start, startSpeed, endSpeed, time, accel, distance);
}

void StepperPath::calculatePhaseFromEndSpeed(FLOAT_T endSpeed, FLOAT_T distance, FLOAT_T time) {
  if (distance == 0 || time == 0) {
    return;
  }

  const FLOAT_T startSpeed = 2.0 * distance / time - endSpeed;
  const FLOAT_T accel = 2.0 * (endSpeed * time - distance) / (time * time);

 // assert(std::abs(startSpeed) > std::abs(endSpeed));
  assert(std::signbit(accel) == std::signbit(endSpeed - startSpeed));

  calculatePhase(PrimarySpeed::End, startSpeed, endSpeed, time, accel, distance);
}

void StepperPath::calculateCruisePhase(const FLOAT_T distance, const FLOAT_T time) {
  if (distance == 0 || time == 0) {
    return;
  }

  PathPhase result = {};

  result.primarySpeed = PrimarySpeed::None;
  result.constant = true;
  result.rampDir = true;
  result.direction = distance > 0 ? StepDirection::Forward : StepDirection::Backward;
  result.initialDelay = time / std::abs(distance);
  result.numSteps = std::abs(distance);
  result.startSpeed = result.endSpeed = distance / time;
  result.time = time;

  phases.push_back(result);
}

void StepperPath::calculatePhase(const PrimarySpeed primarySpeed, const FLOAT_T startSpeed, const FLOAT_T endSpeed, const FLOAT_T time, const FLOAT_T accel, const FLOAT_T distance) {
  PathPhase result = {};

  result.time = time;

  assert(time >= 0);

  if (time == 0 || distance == 0) {
    // no phase to calculate
    return;
  }
  else if (std::signbit(startSpeed) != std::signbit(endSpeed) && startSpeed != 0.0 && endSpeed != 0.0) {
    FLOAT_T firstTime = -startSpeed / accel;
    FLOAT_T secondTime = time - firstTime;
    FLOAT_T firstSteps = startSpeed / 2.0 * firstTime;
    FLOAT_T secondSteps = endSpeed / 2.0 * secondTime;

    assert(std::abs(firstSteps + secondSteps - distance) < CPU_CYCLE_LENGTH);

    assert(firstTime >= 0);

    assert(std::abs(firstTime + endSpeed / accel - time) < CPU_CYCLE_LENGTH);

    calculatePhase(PrimarySpeed::End, startSpeed, 0, firstTime, accel, firstSteps);
    calculatePhase(PrimarySpeed::Start, 0, endSpeed, secondTime, accel, secondSteps);
    return;
  }
  else {
    result.constant = startSpeed == endSpeed;
    result.startSpeed = startSpeed;
    result.endSpeed = endSpeed;
    result.primarySpeed = primarySpeed;

    assert(std::signbit(startSpeed) == std::signbit(endSpeed) || startSpeed == 0.0 || endSpeed == 0.0);
    result.rampDir = std::abs(startSpeed) < std::abs(endSpeed);

    assert(!(startSpeed == 0.0 && endSpeed == 0.0));

    if (startSpeed != 0.0) {
      result.direction = startSpeed > 0.0 ? StepDirection::Forward : StepDirection::Backward;
      assert(std::signbit(startSpeed) == std::signbit(distance));
    }
    else {
      result.direction = endSpeed > 0.0 ? StepDirection::Forward : StepDirection::Backward;
      assert(std::signbit(endSpeed) == std::signbit(distance));
    }

    if (result.constant) {
      assert(result.direction != StepDirection::None);
      result.initialDelay = time / std::abs(distance);
      result.numSteps = std::abs(distance);
    }
    else {
      // see calculateDelayAfterStep for an explanation of these formulas
      result.initialDelay = std::sqrt(2.0 / std::abs(accel));
      result.firstRampStep = result.rampDir ? startSpeed * startSpeed / (2.0 * std::abs(accel)) : endSpeed * endSpeed / (2.0 * std::abs(accel));

      assert(result.firstRampStep >= 0);

      result.numSteps = std::abs(distance);
      assert(result.numSteps >= 0);
    }
  }

  assert(result.initialDelay != 0 && !std::isnan(result.initialDelay) && std::isfinite(result.initialDelay));
  phases.push_back(result);
}

StepperPathState StepperPath::calculateNextStep(StepperPathState state, FLOAT_T currentStep, FLOAT_T stepLength) const {
  assert(state.currentPhase >= 0 && state.currentPhase < (int)phases.size());
  const PathPhase& phase = phases[state.currentPhase];
  FLOAT_T stepWithinPhase = currentStep - state.currentPhaseStartStep;
  
  // first we deal with some possible small numeric errors
  // (*shakes fist menacingly at IEEE floating point*)
  if (stepWithinPhase > phase.numSteps) {
    assert(stepWithinPhase - phase.numSteps < NEGLIGIBLE_ERROR);
    stepWithinPhase = phase.numSteps;
  }

  if (stepWithinPhase < 0) {
    assert(stepWithinPhase > -NEGLIGIBLE_ERROR);
    stepWithinPhase = 0;
  }

  FLOAT_T fractionInPhase = stepLength;
  FLOAT_T remainingFraction = 0.0;

  assert(stepWithinPhase >= 0);

  if(stepWithinPhase + stepLength >= phase.numSteps) {
    // This step ends after this phase is already done.
    fractionInPhase = phase.numSteps - stepWithinPhase;
    remainingFraction = stepWithinPhase + stepLength - phase.numSteps;
  }

  if (fractionInPhase < 0) {
    assert(fractionInPhase > -NEGLIGIBLE_ERROR);
    fractionInPhase = 0;
  }

  if (fractionInPhase > stepLength) {
    assert(fractionInPhase - stepLength < NEGLIGIBLE_ERROR);
    fractionInPhase = stepLength;
  }

  FLOAT_T contribution = calculateDelayAfterStep(phase, std::max(stepWithinPhase, 0.0), fractionInPhase);
  assert(contribution >= 0);
  state.lastStepTime += contribution;

  assert(!std::isnan(state.lastStepTime) && state.lastStepTime >= 0);

  if (remainingFraction > 0) {
    state.currentPhase++;
    assert(state.currentPhase < (int)phases.size());
    state.currentPhaseStartStep += phase.numSteps;

    assert(std::abs(state.lastStepTime - state.currentPhaseStartTime - phase.time) < CPU_CYCLE_LENGTH);
    state.currentPhaseStartTime = state.lastStepTime;

    assert(std::abs(state.currentPhaseStartStep - currentStep - fractionInPhase - (stepWithinPhase < 0 ? -stepWithinPhase : 0.0)) < CPU_CYCLE_LENGTH);
    return calculateNextStep(state, state.currentPhaseStartStep, remainingFraction);
  }
  else {
    return state;
  }
}

/*
 * This is really the core of the this path planner. It operates on math from http://www.atmel.com/Images/doc8017.pdf
 * (in particular, section 2.3.1 on page 5 and section 5.1 on page 14).
 * We describe the notion of an "acceleration ramp" as velocity over time with constant acceleration.
 * The ramp always starts with v=0 and has a slope determined by the needed acceleration.
 * Given such a ramp, the delay after each step is described by:
 *
 * delay = sqrt(2.0 / accel) * (sqrt(step + 1) - sqrt(step))
 *
 * We use this to calculate initialDelay, which is the delay when step = 0:
 *
 * initialDelay = sqrt(2.0 / accel)
 *
 * This number is calculated in advance and stored in PathPhase.
 * We can then re-use this number for the other steps:
 *
 * delay = initialDelay * (sqrt(step + 1) - sqrt(step))
 *
 * There are a few other contortions because we need to decelerate and we don't generally
 * start or end with zero speed.
 * The latter is easy to get around by calculating our starting step on the acceleration ramp:
 *
 * firstRampStep = startSpeed * startSpeed / (2.0 * accel)
 *
 * (This isn't an explicit formula in the paper, but it can be derived by combining
 * t = sqrt(2.0 * n / accel) and v = a*t)
 *
 * And we achieve deceleration by moving backwards on the acceleration ramp.
 */
FLOAT_T StepperPath::calculateDelayAfterStep(const PathPhase& phase, FLOAT_T stepWithinPhase, FLOAT_T stepLength) const {
  if (phase.constant) {
    return phase.initialDelay * stepLength;
  }
  else {
    assert(phase.numSteps - stepWithinPhase - stepLength >= 0);
    // If we're actually decelerating (phase.rampDir == false), we need to move backwards on the acceleration ramp.
    FLOAT_T accelRampStep = (phase.rampDir ? phase.firstRampStep + stepWithinPhase : phase.firstRampStep + (phase.numSteps - stepWithinPhase) - stepLength);

    assert(accelRampStep >= 0);

    FLOAT_T newStep = phase.initialDelay * (std::sqrt(accelRampStep + stepLength) - std::sqrt(accelRampStep));
    assert(newStep >= 0 && !std::isnan(newStep));

    return newStep;
  }
}

StepDirection StepperPath::stepDirection(StepperPathState& state) const {
  return phases[state.currentPhase].direction;
}

int StepperPath::getNumSteps() const {
  return numSteps;
}

std::string StepperPath::toString() const {
  std::stringstream stream;

  for (const PathPhase& phase : phases) {
    std::string direction;

    switch (phase.direction) {
    case StepDirection::None:
      direction = "None";
      break;
    case StepDirection::Forward:
      direction = "Forward";
      break;
    case StepDirection::Backward:
      direction = "Backward";
      break;
    default:
      assert(0);
      direction = "Unknown";
      break;
    }

    std::string primarySpeed;

    switch (phase.primarySpeed) {
    case PrimarySpeed::Start:
      primarySpeed = "Start";
      break;
    case PrimarySpeed::End:
      primarySpeed = "End";
      break;
    case PrimarySpeed::None:
      primarySpeed = "None";
      break;
    }

    stream << "constant: " << phase.constant << " step dir: " << direction << " primarySpeed: " << primarySpeed;
    stream << " startSpeed: " << phase.startSpeed << " endSpeed: " << phase.endSpeed << " numSteps: " << phase.numSteps;
    stream << " time: " << phase.time;

    if (phase.constant) {
      stream << " interval: " << phase.initialDelay;
    }
    else {
      stream << " firstRampStep: " << phase.firstRampStep << " initialDelay: " << phase.initialDelay;
      stream << " rampDir: " << phase.rampDir;
    }

    stream << std::endl;
  }

  return stream.str();
}

bool StepperPath::isInFinalPhase(const StepperPathState& state, FLOAT_T stepNumber) const {
  if (state.currentPhase == (int)phases.size() - 1) {
    return true;
  }
  
  // It's still okay if we're a negligible distance from the final phase

  const PathPhase phase = phases[state.currentPhase];
  const FLOAT_T stepWithinPhase = stepNumber - state.currentPhaseStartStep;
  FLOAT_T fractionRemaining = phase.numSteps - stepWithinPhase;

  // Would the next step have fallen completely in the final phase?
  if (fractionRemaining < 0 && state.currentPhase == (int)phases.size() - 2) {
    return true;
  }

  LOG("missed the final phase by " << fractionRemaining << " steps" << std::endl);

  return fractionRemaining < NEGLIGIBLE_ERROR;
}