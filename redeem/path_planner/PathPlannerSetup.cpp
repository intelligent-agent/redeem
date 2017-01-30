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

#include "PathPlanner.h"

void PathPlanner::setPrintMoveBufferWait(int dt) {
  printMoveBufferWait = dt;
}

void PathPlanner::setMaxBufferedMoveTime(long long dt) {
  maxBufferedMoveTime = dt;
}

// Speeds / accels
void PathPlanner::setMaxSpeeds(VectorN speeds){
  maxSpeeds = speeds;
}

void PathPlanner::setMinSpeeds(VectorN speeds){
  minSpeeds = speeds;
}

void PathPlanner::setAcceleration(VectorN accel){
  maxAccelerationMPerSquareSecond = accel;

  recomputeParameters();
}

void PathPlanner::setJerks(VectorN jerks){
  maxJerks = jerks;

}

void PathPlanner::setAxisStepsPerMeter(VectorN stepPerM) {
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

// bed compensation
void PathPlanner::setBedCompensationMatrix(std::vector<FLOAT_T> matrix)
{
  matrix_bed_comp = matrix;
}
    
// maximum path length
void PathPlanner::setMaxPathLength(FLOAT_T maxLength)
{
  max_path_length = maxLength;
}

// axis configuration
void PathPlanner::setAxisConfig(int axis)
{
  axis_config = axis;
}

// the state of the machine
void PathPlanner::setState(VectorN set)
{
  applyBedCompensation(set);
  state = set;
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
