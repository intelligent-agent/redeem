
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

#include "Delta.h"
#include "Logger.h"
#include "Path.h"
#include <algorithm>
#include <cmath>
#include <numeric>

void calculateLinearMove(const int axis, const int startStep, const int endStep, const double time, std::vector<Step>& steps)
{
    const double distance = endStep - startStep;

    const bool direction = startStep < endStep;
    const int stepIncrement = direction ? 1 : -1;
    const double stepOffset = stepIncrement / 2.0;

    int step = startStep;

    steps.reserve(std::abs(endStep - startStep));

    while (step != endStep)
    {
        const double position = step + stepOffset;
        const double stepTime = (position - startStep) / distance * time;

        assert(stepTime > 0 && stepTime < time);
        assert(steps.empty() || stepTime > steps.back().time);

        steps.emplace_back(Step(stepTime, axis, direction));

        step += stepIncrement;
    }
}

void calculateXYMove(const IntVector3& start, const IntVector3& end, const Vector3& stepsPerM, double time, std::array<std::vector<Step>, NUM_AXES>& steps)
{
    for (int i = 0; i < NUM_MOVING_AXES; i++)
    {
        calculateLinearMove(i, start[i], end[i], time, steps[i]);
    }
}

void calculateExtruderMove(const IntVectorN& start, const IntVectorN& end, double time, std::array<std::vector<Step>, NUM_AXES>& steps)
{
    for (int i = NUM_MOVING_AXES; i < NUM_AXES; i++)
    {
        calculateLinearMove(i, start[i], end[i], time, steps[i]);
    }
}

void Path::zero()
{
    joinFlags = 0;
    flags = 0;
    maxJunctionSpeed = 0;

    distance = 0;
    moveMask = 0;
    timeInTicks = 0;
    speeds.zero();
    worldMove.zero();
    fullSpeed = 0;
    startSpeed = 0;
    endSpeed = 0;
    accel = 0;
    startMachinePos.zero();

    stepperPath.zero();

    for (auto& stepVector : steps)
    {
        std::vector<Step> empty;
        stepVector.swap(empty);
    }
}

Path::Path()
{
    zero();
}

Path::Path(Path&& path)
{
    *this = std::move(path);
}

Path& Path::operator=(Path&& path)
{
    // move assignment operator
    joinFlags = path.joinFlags;
    flags = path.flags.load();
    maxJunctionSpeed = path.maxJunctionSpeed;

    distance = path.distance;
    moveMask = path.moveMask;
    timeInTicks = path.timeInTicks;
    speeds = path.speeds;
    worldMove = path.worldMove;
    fullSpeed = path.fullSpeed;
    startSpeed = path.startSpeed;
    endSpeed = path.endSpeed;
    accel = path.accel;
    startMachinePos = path.startMachinePos;

    stepperPath = path.stepperPath;
    steps = std::move(path.steps);

    return *this;
}

inline static double calculateMaximumSpeedInternal(const VectorN& worldMove, const VectorN& maxSpeeds, const double distance)
{
    // First we need to figure out the minimum time for the move.
    // We determine this by calculating how long each axis would take to complete its move
    // at its maximum speed.
    double minimumTimeForMove = 0;

    for (int i = 0; i < NUM_AXES; i++)
    {
        if (worldMove[i])
        {
            double minimumAxisTimeForMove = fabs(worldMove[i]) / maxSpeeds[i]; // m / (m/s) = s
            LOG("axis " << i << " needs to travel " << worldMove[i] << " at a maximum of " << maxSpeeds[i] << " which would take " << minimumAxisTimeForMove << std::endl);
            minimumTimeForMove = std::max(minimumTimeForMove, minimumAxisTimeForMove);
        }
    }

    return distance / minimumTimeForMove;
}

inline static double calculateMaximumSpeed(const VectorN& worldMove, const VectorN& maxSpeeds, const double distance, int axisConfig)
{
    if (axisConfig == AXIS_CONFIG_DELTA)
    {
        // Fold the entire XYZ distance into X
        VectorN fakeWorldMove(worldMove);
        fakeWorldMove[0] = vabs(fakeWorldMove.toVector3());
        fakeWorldMove[1] = 0;
        fakeWorldMove[2] = 0;

        return calculateMaximumSpeedInternal(fakeWorldMove, maxSpeeds, distance);
    }
    else if (axisConfig == AXIS_CONFIG_CORE_XY || axisConfig == AXIS_CONFIG_H_BELT)
    {
        // Fold the XY distance into X
        VectorN fakeWorldMove(worldMove);
        fakeWorldMove[0] = vabs(Vector3(fakeWorldMove[0], fakeWorldMove[1], 0));
        fakeWorldMove[1] = 0;

        return calculateMaximumSpeedInternal(fakeWorldMove, maxSpeeds, distance);
    }
    else
    {
        return calculateMaximumSpeedInternal(worldMove, maxSpeeds, distance);
    }
}

void Path::initialize(const IntVectorN& machineStart,
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
    bool is_probe)
{
    this->zero();

    const IntVectorN machineMove = machineEnd - machineStart;
    worldMove = worldEnd - worldStart;
    distance = vabs(worldMove);
    startMachinePos = machineStart;

    joinFlags = 0;
    flags = (cancelable ? FLAG_CANCELABLE : 0) | (is_probe ? FLAG_PROBE : 0);

    assert(!std::isnan(distance));

    for (int axis = 0; axis < NUM_AXES; axis++)
    {
        if (machineMove[axis] != 0)
        {
            moveMask |= (1 << axis);
        }
    }

    // Now figure out if we can honor the user's requested speed.
    fullSpeed = std::min(requestedSpeed, calculateMaximumSpeed(worldMove, maxSpeeds, distance, axisConfig));
    assert(!std::isnan(fullSpeed));

    const double idealTimeForMove = distance / fullSpeed; // m / (m/s) = s
    timeInTicks = (unsigned long long)(F_CPU * idealTimeForMove); // ticks / s * s = ticks

    for (int i = 0; i < NUM_AXES; i++)
    {
        if (worldMove[i])
        {
            speeds[i] = worldMove[i] / idealTimeForMove;
        }
        else
        {
            speeds[i] = 0;
        }
    }

    // As it turns out, this function can also calculate accel if we give it values that are all derivatives of what it normally wants
    accel = std::min(requestedAccel, calculateMaximumSpeed(speeds, maxAccelMPerSquareSecond, fullSpeed, axisConfig));

    // Calculate whether we're guaranteed to reach cruising speed.
    double maximumAccelTime = fullSpeed / accel; // (m/s) / (m/s^2) = s
    double maximumAccelDistance = maximumAccelTime * (fullSpeed / 2.0);
    if (2.0 * maximumAccelDistance < distance)
    {
        // This move has enough distance that we can accelerate from 0 to fullSpeed and back to 0.
        // We'll definitely hit cruising speed.
        flags |= FLAG_WILL_REACH_FULL_SPEED;
    }

    LOG("ideal move should be " << fullSpeed << " m/s and cover " << distance << " m in " << idealTimeForMove << " seconds" << std::endl);

    switch (axisConfig)
    {
    case AXIS_CONFIG_DELTA:
        delta.calculateMove(machineStart.toIntVector3(), machineEnd.toIntVector3(), stepsPerM.toVector3(), idealTimeForMove, steps);
        break;
    case AXIS_CONFIG_XY:
    case AXIS_CONFIG_H_BELT:
    case AXIS_CONFIG_CORE_XY:
        calculateXYMove(machineStart.toIntVector3(), machineEnd.toIntVector3(), stepsPerM.toVector3(), idealTimeForMove, steps);
        break;
    default:
        assert(0);
    }

    calculateExtruderMove(machineStart, machineEnd, idealTimeForMove, steps);

    assert(!steps.empty());

    if ((isAxisMove(E_AXIS) && !isAxisOnlyMove(E_AXIS)) || (isAxisMove(H_AXIS) && !isAxisOnlyMove(H_AXIS)))
    {
        flags |= FLAG_USE_PRESSURE_ADVANCE;
    }

    LOG("Distance in m:     " << distance << std::endl);
    LOG("Speed in m/s:      " << fullSpeed << " requested: " << requestedSpeed << std::endl);
    LOG("Accel in m/s:     " << accel << " requested: " << requestedAccel << std::endl);
    LOG("Ticks :            " << timeInTicks << std::endl);

    invalidateStepperPathParameters();
}

double Path::runFinalStepCalculations()
{
    updateStepperPathParameters();

    for (auto& axisSteps : steps)
    {
        for (auto& step : axisSteps)
        {
            step.time = stepperPath.dilateTime(step.time);
        }
    }

    LOG("accelSteps: " << stepperPath.accelSteps
                       << " cruiseSteps: " << stepperPath.cruiseSteps
                       << " decelSteps: " << stepperPath.decelSteps << std::endl);

    return stepperPath.finalTime();
}

/** Update parameter used by updateTrapezoids

Computes the acceleration/decelleration steps and advanced parameter associated.
*/
void Path::updateStepperPathParameters()
{
    if (areParameterUpToDate())
        return;

    double cruiseSpeed = fullSpeed;

    double accelTime = (fullSpeed - startSpeed) / accel;
    double decelTime = (fullSpeed - endSpeed) / accel;

    double accelDistance = (cruiseSpeed * cruiseSpeed - startSpeed * startSpeed) / (2.0 * accel);
    double decelDistance = (cruiseSpeed * cruiseSpeed - endSpeed * endSpeed) / (2.0 * accel);
    assert(accelDistance >= 0);
    assert(decelDistance >= 0);

    double cruiseDistance = distance - accelDistance - decelDistance;
    double cruiseTime = cruiseDistance / cruiseSpeed;

    if (accelDistance + decelDistance > distance)
    {
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

        if (cruiseDistance < 0)
        {
            // As it turns out, the optimizer can over-accelerate on very short moves because it
            // doesn't check that the end speed of a move is reachable from the start speed within
            // limits. This hasn't been a problem because it only affects moves that are only a few
            // steps in the first place. However, when it occurs, this assert will fire.
            assert(std::abs(cruiseDistance) < NEGLIGIBLE_ERROR);

            if (accelDistance == 0)
            {
                assert(accelTime == 0);

                cruiseDistance = 0;
                cruiseTime = 0;
                cruiseSpeed = startSpeed;

                decelDistance = distance;
                decelTime = distance / ((cruiseSpeed + endSpeed) / 2.0);
            }
            else if (decelDistance == 0)
            {
                assert(decelTime == 0);

                cruiseDistance = 0;
                cruiseTime = 0;
                cruiseSpeed = endSpeed;

                accelDistance = distance;
                accelTime = distance / ((cruiseSpeed + startSpeed) / 2.0);
            }
            else
            {
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

    stepperPath.baseSpeed = fullSpeed;
    stepperPath.startSpeed = startSpeed;
    stepperPath.cruiseSpeed = cruiseSpeed;
    stepperPath.endSpeed = endSpeed;
    stepperPath.accel = accel;
    stepperPath.distance = distance;

    const double& Vi = startSpeed;
    const double& Vc = cruiseSpeed;
    const double& Vf = endSpeed;
    const double& A = accel;
    const double& D = distance;

    const double Vi2 = Vi * Vi;
    const double Vc2 = Vc * Vc;
    const double Vf2 = Vf * Vf;

    stepperPath.baseAccelEnd = (-(Vi2 - Vc2)) / (2 * A * Vc);
    stepperPath.baseCruiseEnd = (Vf2 - Vc2 + 2 * A * D) / (2 * A * Vc);
    stepperPath.baseMoveEnd = D / Vc;

    stepperPath.moveEnd = (Vi2 - 2 * Vc * Vi + Vf2 - 2 * Vc * Vf + 2 * Vc2 + 2 * A * D) / (2 * A * Vc);

    joinFlags |= FLAG_JOIN_STEPPARAMS_COMPUTED;

    assert(areParameterUpToDate());
}

double StepperPathParameters::dilateTime(double t) const
{
    const double& Vi = startSpeed;
    const double& Vc = cruiseSpeed;
    const double& Vf = endSpeed;
    const double& A = accel;
    const double& D = distance;

    const double Vi2 = Vi * Vi;
    const double Vc2 = Vc * Vc;
    const double Vf2 = Vf * Vf;

    assert(t >= 0);

    t *= baseSpeed / cruiseSpeed;

    double result = NAN;

    if (t < baseAccelEnd)
    {
        accelSteps++;
        result = (sqrt(2 * A * Vc * t + Vi2) - Vi) / A;
    }
    else if (t < baseCruiseEnd)
    {
        cruiseSteps++;
        result = (2 * A * Vc * t + Vi2 + (-2) * Vc * Vi + Vc2) / (2 * A * Vc);
    }
    else if (t < baseMoveEnd)
    {
        decelSteps++;
        result = (-(2 * Vc * sqrt((-2) * A * Vc * t + Vf2 + 2 * A * D) - Vi2 + 2 * Vc * Vi - Vf2 + (-2) * Vc2 + (-2) * A * D)) / (2 * A * Vc);
    }
    else
    {
        assert(0);
    }

    assert(!std::isnan(result));

    return result;
}

double StepperPathParameters::finalTime() const
{
    return moveEnd;
}
