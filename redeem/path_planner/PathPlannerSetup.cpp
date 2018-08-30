/*
  This file is part of Redeem - 3D Printer control software
 
  Author: Mathieu Monney
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

#include "AlarmCallback.h"
#include "PathPlanner.h"

// Speeds / accels
void PathPlanner::setMaxSpeeds(VectorN speeds)
{
    maxSpeeds = speeds;
}

void PathPlanner::setAcceleration(VectorN accel)
{
    maxAccelerationMPerSquareSecond = accel;

    recomputeParameters();
}

void PathPlanner::setMaxSpeedJumps(VectorN speedJumps)
{
    optimizer.setMaxSpeedJumps(speedJumps);
}

void PathPlanner::setAxisStepsPerMeter(VectorN stepPerM)
{
    axisStepsPerM = stepPerM;

    recomputeParameters();
}

// soft endstops
void PathPlanner::setSoftEndstopsMin(VectorN stops)
{
    soft_endstops_min = stops;
}

void PathPlanner::setSoftEndstopsMax(VectorN stops)
{
    soft_endstops_max = stops;
}

void PathPlanner::setStopPrintOnSoftEndstopHit(bool stop)
{
    stop_on_soft_endstops_hit = stop;
}

void PathPlanner::setStopPrintOnPhysicalEndstopHit(bool stop)
{
    stop_on_physical_endstops_hit = stop;
}

// bed compensation
void PathPlanner::setBedCompensationMatrix(std::vector<double> matrix)
{
    matrix_bed_comp = matrix;
}

// axis configuration
void PathPlanner::setAxisConfig(int axis)
{
    if (axis_config != axis)
    {
        VectorN stateBefore = getState();

        axis_config = axis;

        setState(stateBefore);
    }
}

void PathPlanner::pruAlarmCallback()
{
    if (stop_on_physical_endstops_hit)
    {
        LOGCRITICAL("PRU fired endstop alarm - disabling path planner and firing alarm" << std::endl);
        acceptingPaths = false;
    }
    else
    {
        LOGCRITICAL("PRU fired endstop alarm - continuing path planner and firing alarm" << std::endl);
    }
    alarmCallback.call(7, "Physical Endstop hit", "Physical Endstop hit");
}

// the state of the machine
void PathPlanner::setState(VectorN set)
{
    applyBedCompensation(set);

    IntVectorN newState = (set * axisStepsPerM).round();

    switch (axis_config)
    {
    case AXIS_CONFIG_XY:
        break;
    case AXIS_CONFIG_H_BELT:
    {
        const Vector3 motionPos = worldToHBelt(set.toVector3());
        const IntVector3 motionMotorPos = (motionPos * axisStepsPerM.toVector3()).round();
        newState[0] = motionMotorPos.x;
        newState[1] = motionMotorPos.y;
        newState[2] = motionMotorPos.z;
        break;
    }
    case AXIS_CONFIG_CORE_XY:
    {
        const Vector3 motionPos = worldToCoreXY(set.toVector3());
        const IntVector3 motionMotorPos = (motionPos * axisStepsPerM.toVector3()).round();
        newState[0] = motionMotorPos.x;
        newState[1] = motionMotorPos.y;
        newState[2] = motionMotorPos.z;
        break;
    }
    case AXIS_CONFIG_DELTA:
    {
        const Vector3 motionPos = delta_bot.worldToDelta(set.toVector3());
        const IntVector3 motionMotorPos = (motionPos * axisStepsPerM.toVector3()).round();
        newState[0] = motionMotorPos.x;
        newState[1] = motionMotorPos.y;
        newState[2] = motionMotorPos.z;
        break;
    }

    default:
        assert(0);
    }

    state = newState;
}

// slaves
bool has_slaves;
std::vector<int> master;
std::vector<int> slave;

void PathPlanner::enableSlaves(bool enable)
{
    has_slaves = enable;
}

void PathPlanner::addSlave(int master_in, int slave_in)
{
    master.push_back(master_in);
    slave.push_back(slave_in);

    axes_stepping_together[master_in] |= (1 << slave_in);
}

// backlash compensation
void PathPlanner::setBacklashCompensation(VectorN set)
{
    backlash_compensation = set;
}

void PathPlanner::resetBacklash()
{
    backlash_state.zero();
}

double PathPlanner::getLastProbeDistance()
{
    return lastProbeDistance;
}
