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

void PathPlanner::setMinBufferedMoveTime(int dt) {
  minBufferedMoveTime = dt;
}

void PathPlanner::setMaxBufferedMoveTime(int dt) {
  maxBufferedMoveTime = dt;
}

// Speeds / accels
void PathPlanner::setMaxSpeeds(std::vector<FLOAT_T> speeds){
  if ( speeds.size() != NUM_AXES ) {throw InputSizeError();}
  maxSpeeds = speeds;
}

void PathPlanner::setMinSpeeds(std::vector<FLOAT_T> speeds){
  if ( speeds.size() != NUM_AXES ) {throw InputSizeError();}
  minSpeeds = speeds;
}

void PathPlanner::setAcceleration(std::vector<FLOAT_T> accel){
  if ( accel.size() != NUM_AXES ) {throw InputSizeError();}

  maxAccelerationMPerSquareSecond = accel;

  recomputeParameters();
}

void PathPlanner::setJerks(std::vector<FLOAT_T> jerks){
  if ( jerks.size() != NUM_AXES ) {throw InputSizeError();}

  maxJerks = jerks;

}

void PathPlanner::setAxisStepsPerMeter(std::vector<FLOAT_T> stepPerM) {
  if ( stepPerM.size() != NUM_AXES ) {throw InputSizeError();}

  axisStepsPerM = stepPerM;

  recomputeParameters();
}

// soft endstops
void PathPlanner::setSoftEndstopsMin(std::vector<FLOAT_T> stops)
{
  if ( stops.size() != NUM_AXES ) {throw InputSizeError();}
  soft_endstops_min = stops;
}

void PathPlanner::setSoftEndstopsMax(std::vector<FLOAT_T> stops)
{ 
 if ( stops.size() != NUM_AXES ) {throw InputSizeError();}
  soft_endstops_max = stops;
}

// bed compensation
void PathPlanner::setBedCompensationMatrix(std::vector<FLOAT_T> matrix)
{
  if ( matrix.size() != 9 ) {throw InputSizeError();}
  
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
void PathPlanner::setState(std::vector<FLOAT_T> set)
{
  if ( set.size() != NUM_AXES ) {throw InputSizeError();}
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
void PathPlanner::setBacklashCompensation(std::vector<FLOAT_T> set)
{
  if ( set.size() != NUM_AXES ) {throw InputSizeError();}
  backlash_compensation = set;
}

void PathPlanner::resetBacklash()
{
  for (FLOAT_T& bs : backlash_state) {
    bs = 0.0;
  }
}
