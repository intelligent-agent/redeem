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

int PathPlanner::softEndStopApply(const VectorN &startPos, const VectorN &endPos)
{
  for (size_t i = 0; i<NUM_AXES; ++i) {
    if (startPos[i] < soft_endstops_min[i]) {
      LOGERROR( "queueMove FAILED: axis " << i 
		<< " start position outside of soft limit (start = " << startPos[i] 
		<< ", min limit = " << soft_endstops_min[i] << ")\n");
      return 1;
    } else if (startPos[i] > soft_endstops_max[i]) {
      LOGERROR( "queueMove FAILED: axis " << i 
		<< " start position outside of soft limit (start = " << startPos[i] 
		<< ", max limit = " << soft_endstops_max[i] << ")\n");
      return 1;
    } else if (endPos[i] < soft_endstops_min[i]) {
      LOGERROR( "queueMove FAILED: axis " << i 
		<< " end position outside of soft limit (end = " << endPos[i] 
		<< ", min limit = " << soft_endstops_min[i] << ")\n");
      return 1;
    } else if (endPos[i] > soft_endstops_max[i]) {
      LOGERROR( "queueMove FAILED: axis " << i 
		<< " end position outside of soft limit (end = " << endPos[i] 
		<< ", max limit = " << soft_endstops_max[i] << ")\n");
      return 1;
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

int PathPlanner::splitInput(const VectorN startPos, const VectorN vec,
			    FLOAT_T speed, FLOAT_T accel, bool cancelable, bool optimize,
			    bool use_backlash_compensation, int tool_axis, bool virgin)
{

  // check if the path needs to be split

  if (axis_config != AXIS_CONFIG_DELTA) {
    return 0;
  }
    
  FLOAT_T xy2, z2, mag;
  xy2 = vec[0]*vec[0] + vec[1]*vec[1];
  z2 = vec[2]*vec[2];
  mag = sqrt(xy2);
    

  // if the path has no movement in the xy plane then it doesn't need to be split
  if (mag <= max_path_length) {
    return 0;
  }
     
  mag = sqrt(xy2 + z2);
	
  if (mag > max_path_length) {
    if (!virgin) {
      LOG("tried to double-split path: XY length: " << mag << " max length: " << max_path_length << std::endl);
      //assert(virgin);
    }
        
    // how many segments are needed
    long N = std::lround(std::ceil(mag / max_path_length));
        
    LOG("move split into " << N << " pieces\n");
		
    // the sub segments
    VectorN sub_start(startPos);
    VectorN sub_stop;
		
    for (long i=0; i < N; ++i) {
      VectorN sub_vec;
			
      // calculate the end point of the segment
      for (size_t j=0; j<NUM_AXES; ++j) {
	sub_stop[j] = startPos[j] + vec[j]*(i+1)/N;
	sub_vec[j] = sub_stop[j] - sub_start[j];
      }

      FLOAT_T sub_mag = std::sqrt(sub_vec[0] * sub_vec[0] + sub_vec[1] * sub_vec[1] + sub_vec[2] * sub_vec[2]);
      if (sub_mag > max_path_length && sub_mag - max_path_length > NEGLIGIBLE_ERROR) {
	LOGERROR("split didn't actually get us below the max length: " << sub_mag << " vs " << max_path_length << std::endl);
	LOGERROR("splitting " << mag << " into " << N << " pieces." << std::endl);
	assert(sub_mag <= max_path_length);
      }
      else {
	LOG("segment length: " << sub_mag << std::endl);
      }
			
      // queue the segment
      // most of the options are false as they have already been 
      // handled by the processing of the overall path that is now 
      // being split. We do, however, need to pass on whether we 
      // are applying backlash compensation and the tool axis
      // as these modifiers are applied at the end.
      queueMove(sub_start, sub_stop, speed, accel, cancelable, 
		optimize, false, false, use_backlash_compensation, 
		tool_axis, false);
			
      // load the end point in as the next starting point
      sub_start = sub_stop;
    }
		
    // return so we don't continue adding this path
    return 1;
  }
    
  return 0;
}

void PathPlanner::transformVector(VectorN &vec, const VectorN &startPos)
{
  if (axis_config == AXIS_CONFIG_DELTA) {

    FLOAT_T start_x, start_y, start_z;
        
    if (hasEndABC) {
      start_x = endABC[0];
      start_y = endABC[1];
      start_z = endABC[2];
    } else {
      delta_bot.worldToDelta(startPos[0], startPos[1], startPos[2], &start_x, &start_y, &start_z);
    }

    assert(!(std::isnan(endABC[0]) || std::isnan(endABC[1]) || std::isnan(endABC[2])));
        
    startABC[0] = start_x;
    startABC[1] = start_y;
    startABC[2] = start_z;

    assert(!(std::isnan(startABC[0]) || std::isnan(startABC[1]) || std::isnan(startABC[2])));
		
    FLOAT_T end_x, end_y, end_z;
    delta_bot.worldToDelta(startPos[0] + vec[0], startPos[1] + vec[1], startPos[2] + vec[2], &end_x, &end_y, &end_z);
        
    assert(!(std::isnan(end_x) || std::isnan(end_y) || std::isnan(end_z)));
    vec[0] = end_x - start_x;
    vec[1] = end_y - start_y;
    vec[2] = end_z - start_z;
		
  } else {
    if (axis_config == AXIS_CONFIG_H_BELT) {
      FLOAT_T x = -0.5*vec[0] + 0.5*vec[1];
      FLOAT_T y = -0.5*vec[0] - 0.5*vec[1];
      vec[0] = x; vec[1] = y;
    } else if (axis_config == AXIS_CONFIG_CORE_XY) {
      FLOAT_T x = vec[0] + vec[1];
      FLOAT_T y = vec[0] - vec[1];
      vec[0] = x; vec[1] = y;
    }
  }

  return;
}

void PathPlanner::reverseTransformVector(VectorN &vec)
{

  hasEndABC = false;
  if (axis_config == AXIS_CONFIG_DELTA) {
		
    FLOAT_T end_x, end_y, end_z;
		
    end_x = startABC[0] + vec[0];
    end_y = startABC[1] + vec[1];
    end_z = startABC[2] + vec[2];
		
    endABC[0] = end_x;
    endABC[1] = end_y;
    endABC[2] = end_z;

    FLOAT_T start_x, start_y, start_z;
    delta_bot.deltaToWorld(startABC[0], startABC[1], startABC[2], &start_x, &start_y, &start_z);
		
    delta_bot.deltaToWorld(endABC[0], endABC[1], endABC[2], &end_x, &end_y, &end_z);
		
    vec[0] = end_x - start_x;
    vec[1] = end_y - start_y;
    vec[2] = end_z - start_z;
		
  } else {
    if (axis_config == AXIS_CONFIG_H_BELT) {
      FLOAT_T x = -1.0*vec[0] - 1.0*vec[1];
      FLOAT_T y =      vec[0] - 1.0*vec[1];
      vec[0] = x; vec[1] = y;
    } else if (axis_config == AXIS_CONFIG_CORE_XY) {
      FLOAT_T x = 0.5*vec[0] + 0.5*vec[1];
      FLOAT_T y = 0.5*vec[0] - 0.5*vec[1];
      vec[0] = x; vec[1] = y;
    }
  }
	
  return;
}

void PathPlanner::backlashCompensation(VectorN &delta) 
{

  int dirstate;
  for (size_t i = 0; i<NUM_AXES; ++i) {
    dirstate = sgn(delta[i]);
    if ((dirstate != 0) && (dirstate != backlash_state[i])) {
      backlash_state[i] = dirstate;
      delta[i] += dirstate*backlash_compensation[i];
    }
  }
    
  return;
}

void PathPlanner::handleSlaves(VectorN &startPos, VectorN &endPos)
{
  if ( has_slaves) {
    for (size_t i=0; i<master.size(); ++i) {
      startPos[slave[i]] = startPos[master[i]];
      endPos[slave[i]] = endPos[master[i]];
      state[slave[i]] = state[master[i]];
    }
  }
}
