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
#include "PathPlanner.h"

// Return axis num+1 on min hit, axis num + 11 on max.
int PathPlanner::softEndStopApply(const VectorN &endPos)
{
  for (size_t i = 0; i<NUM_AXES; ++i) {
    if (endPos[i] < soft_endstops_min[i]) {
      LOGERROR( "queueMove FAILED: axis " << i 
          << " end position outside of soft limit (end = " << endPos[i] 
          << ", min limit = " << soft_endstops_min[i] << ")\n");
      return i+1;
    } else if (endPos[i] > soft_endstops_max[i]) {
      LOGERROR( "queueMove FAILED: axis " << i 
          << " end position outside of soft limit (end = " << endPos[i] 
          << ", max limit = " << soft_endstops_max[i] << ")\n");
      return i+11;
    }
  }

  return 0;
}

void PathPlanner::applyBedCompensation(VectorN &endPos)
{
  // matrix*vector
  FLOAT_T x = endPos[0]*matrix_bed_comp[0] + endPos[1]*matrix_bed_comp[1] + endPos[2]*matrix_bed_comp[2];
  FLOAT_T y = endPos[0]*matrix_bed_comp[3] + endPos[1]*matrix_bed_comp[4] + endPos[2]*matrix_bed_comp[5];
  FLOAT_T z = endPos[0]*matrix_bed_comp[6] + endPos[1]*matrix_bed_comp[7] + endPos[2]*matrix_bed_comp[8];

  endPos[0] = x;
  endPos[1] = y;
  endPos[2] = z;
        
  return;
}

inline int sgn(long long val) { return (0 < val) - (val < 0); }

void PathPlanner::backlashCompensation(IntVectorN &delta)
{
  int dirstate;
  for (size_t i = 0; i<NUM_AXES; ++i) {
    dirstate = sgn(delta[i]);
    if ((dirstate != 0) && (dirstate != backlash_state[i])) {
      backlash_state[i] = dirstate;
      delta[i] += std::llround(dirstate * backlash_compensation[i] * axisStepsPerM[i]);
    }
  }
  return;
}

void PathPlanner::clearSlaveAxesMovements(VectorN& startWorldPos, VectorN& stopWorldPos)
{
  for (auto axis : slave)
  {
    stopWorldPos[axis] = startWorldPos[axis];
  }
}

Vector3 PathPlanner::worldToHBelt(const Vector3& world)
{
  // A = (-x + y) / 2
  // B = (-x - y) / 2
  return Vector3(0.5 * (-world[0] + world[1]), 0.5 * (-world[0] - world[1]), world[2]);
}

Vector3 PathPlanner::hBeltToWorld(const Vector3& motion)
{
  // x = -A - B
  // y = A - B
  return Vector3(-motion[0] - motion[1], motion[0] - motion[1], motion[2]);
}

Vector3 PathPlanner::worldToCoreXY(const Vector3& world)
{
  // A = x + y
  // B = x - y
  return Vector3(world[0] + world[1], world[0] - world[1], world[2]);
}

Vector3 PathPlanner::coreXYToWorld(const Vector3& motion)
{
  // x = (A + B) / 2
  // y = (A - B) / 2
  return Vector3(0.5 * (motion[0] + motion[1]), 0.5 * (motion[0] - motion[1]), motion[2]);
}
