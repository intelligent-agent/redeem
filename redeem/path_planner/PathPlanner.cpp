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
#include <cmath>
#include <assert.h>
#include <thread>
#include <Python.h>


PathPlanner::PathPlanner(unsigned int cacheSize) {
  linesPos = 0;
  linesWritePos = 0;
  LOG( "PathPlanner " << PATH_PLANNER_VERSION << std::endl);
  moveCacheSize = cacheSize;
  lines.resize(moveCacheSize);
  printMoveBufferWait = 250;
  minBufferedMoveTime = 100;
  maxBufferedMoveTime = 6 * printMoveBufferWait;
  linesCount = 0;
  linesTicksCount = 0;
  stop = false;
  hasEndABC = false;
	
  max_path_length = 1e6;
  axis_config = AXIS_CONFIG_XY;
  has_slaves = false;

  maxSpeeds.resize(NUM_AXES, 0);
  minSpeeds.resize(NUM_AXES, 0);
  maxJerks.resize(NUM_AXES, 0);
  maxAccelerationStepsPerSquareSecond.resize(NUM_AXES, 0);
  maxAccelerationMPerSquareSecond.resize(NUM_AXES, 0);
  axisStepsPerM.resize(NUM_AXES, 0);
	
  soft_endstops_min.resize(NUM_AXES, 0);
  soft_endstops_max.resize(NUM_AXES, 0);
  state.resize(NUM_AXES, 0);
  backlash_compensation.resize(NUM_AXES, 0);
  backlash_state.resize(NUM_AXES, 0);
	
  // set bed compensation matrix to identity
  matrix_bed_comp.resize(9, 0);
  matrix_bed_comp[0] = 1.0;
  matrix_bed_comp[4] = 1.0;
  matrix_bed_comp[8] = 1.0;
	
  
  startABC.resize(3, 0);
  endABC.resize(3, 0);

  recomputeParameters();

  LOG( "PathPlanner initialized\n");
}

void PathPlanner::recomputeParameters() {
  for(int i=0; i<NUM_AXES; i++){
    /** Acceleration in steps/s^2 in printing mode.*/
    maxAccelerationStepsPerSquareSecond[i] =  maxAccelerationMPerSquareSecond[i] * axisStepsPerM[i];
  }
}


bool PathPlanner::queueSyncEvent(bool isBlocking /* = true */){
  PyThreadState *_save; 
  _save = PyEval_SaveThread();

  // If the move command buffer isn't empty, make the last line a sync event
  {	
    std::unique_lock<std::mutex> lk(line_mutex);
    if(linesCount > 0){
      unsigned int lastLine = (linesWritePos == 0) ? moveCacheSize - 1 : linesWritePos - 1;
      Path *p = &lines[lastLine];
      p->setSyncEvent(isBlocking);
      PyEval_RestoreThread(_save);
      return true;
    }
  }

  PyEval_RestoreThread(_save);
  return false;	// If the move command buffer is completly empty, it's too late.
}

// Wait for a sync event on the stepper PRU
int PathPlanner::waitUntilSyncEvent(){
  int ret;
  PyThreadState *_save; 
  _save = PyEval_SaveThread();
  ret = pru.waitUntilSync();
  PyEval_RestoreThread(_save);
  return ret;
}
                     
// Clear the sync event on the stepper PRU and resume operation.
void PathPlanner::clearSyncEvent(){
  PyThreadState *_save; 
  _save = PyEval_SaveThread();
  pru.resume();
  PyEval_RestoreThread(_save);
}

void PathPlanner::queueMove(std::vector<FLOAT_T> startPos, std::vector<FLOAT_T> endPos, 
			    FLOAT_T speed, FLOAT_T accel, 
			    bool cancelable, bool optimize, 
			    bool enable_soft_endstops, bool use_bed_matrix, 
			    bool use_backlash_compensation, int tool_axis,
			    bool virgin) 
{

  
  if ( startPos.size() != NUM_AXES ) {throw InputSizeError();}
  if ( endPos.size() != NUM_AXES ) {throw InputSizeError();}

  ////////////////////////////////////////////////////////////////////
  // PRE-PROCESSING
  ////////////////////////////////////////////////////////////////////
	
  LOG("PP: queueMove()\n");
  // for (int i = 0; i<NUM_AXES; ++i) {
  //   LOG("AXIS " << i << ": start = " << startPos[i] << "(" << state[i] << "), end = " << endPos[i] << "\n");
  // }
	
  // If this is a virgin path then we need to perform all 
  // necessary modifications to the end position
  if (virgin) {
    // Cap the end position based on soft end stops
    if ( enable_soft_endstops) {
      if (softEndStopApply(startPos, endPos)) {
        return;
      }
    }
    // Calculate the position to reach, with bed levelling
    if (use_bed_matrix) {
      LOG("Before matrix X: "<<endPos[0]<<" Y: "<<endPos[1]<<" Z: "<<endPos[2]<<"\n");  
      applyBedCompensation(endPos);
      LOG("After matrix X: "<<endPos[0]<<" Y: "<<endPos[1]<<" Z: "<<endPos[2]<<"\n");  
    }
  }
	
  // Get the vector to move us from where we are, to where we ideally want to be. 
    
  std::vector<FLOAT_T> vec(NUM_AXES, 0);
    
  for (size_t i = 0; i<vec.size(); ++i) {
    vec[i] = endPos[i] - state[i];
  }
	
  // Check if the path needs to be split
  if( splitInput(state, vec, speed, accel, cancelable, optimize, use_backlash_compensation, tool_axis) ) {
    return;
  }

  // Calculate the distance in world space and use it to convert the user's world-speed into a desired move time
  FLOAT_T worldDistance = 0;
  for (int i = 0; i < NUM_AXES; i++) {
    worldDistance += vec[i] * vec[i];
  }

  worldDistance = std::sqrt(worldDistance);

  FLOAT_T desiredTime = worldDistance / speed; // m / (m/s) = s

  // Transform the vector according to the movement style of the robot.
  transformVector(vec, state);
    
  // Compute stepper translation, yielding the discrete/rounded distance.
  FLOAT_T num_steps;
  std::vector<FLOAT_T> delta(NUM_AXES, 0);
  FLOAT_T sum_delta = 0.0;
  for (int i = 0; i<NUM_AXES; ++i) {
    num_steps = round(fabs(vec[i])*axisStepsPerM[i]);
    delta[i] = sgn(vec[i])*num_steps/axisStepsPerM[i];
    vec[i] = delta[i];
    sum_delta += fabs(delta[i]);
  }


  // check for a no-move
  if (sum_delta == 0.0) {
    return;
  }
	
  // 'vec' now contains the actual distance travelled, by the motors, 
  // after taking into account the discrete nature of the stepper motors
	
  reverseTransformVector(vec);
	
  // and now vec is back in physical space
	
  // backlash compensation
  if (use_backlash_compensation) {
    backlashCompensation(delta);
  }

  // change startPos and endPos to give the change in position using machine coordinates
  // also update the state of the machine, i.e. where the effector really is in physical space
  for (int i = 0; i<NUM_AXES; ++i) {
    startPos[i] = state[i]; // the real starting position
    endPos[i] =   state[i] + delta[i]; // the real ending position
    state[i] += vec[i]; // update the new state of the machine
  }
    
  // handle any slaving activity
  handleSlaves(startPos, endPos);

  // LOG("MOVE COMMAND:\n");
  // for (int i = 0; i<NUM_AXES; ++i) {
  //   LOG("AXIS " << i << ": start = " << startPos[i] << ", end = " << state[i] << "\n");
  // }
    	
  ////////////////////////////////////////////////////////////////////
  // LOAD INTO QUEUE
  ////////////////////////////////////////////////////////////////////
    
    
  std::vector<FLOAT_T> axis_diff(NUM_AXES, 0);        // Axis movement in m
  PyThreadState *_save; 
  _save = PyEval_SaveThread();

  unsigned int linesQueued = 0;
  unsigned int linesCacheRemaining = 0;
  long long linesTicksRemaining = 0;
  long long linesTicksQueued = 0;

  // wait for the worker
  if(linesCacheRemaining == 0 || linesTicksRemaining == 0){
    std::unique_lock<std::mutex> lk(line_mutex);
    //LOG( "Waiting for free move command space... Current: " << moveCacheSize - linesCount << std::endl);
    lineAvailable.wait(lk, [this]{return stop || (linesCount < moveCacheSize && !isLinesBufferFilled());});
    linesCacheRemaining = moveCacheSize - linesCount;
    linesTicksRemaining = maxBufferedMoveTime - linesTicksCount;
  }	
  if(stop){
    PyEval_RestoreThread(_save);
    LOG( "Stopped/aborted/Cancelled while waiting for free move command space. linesCount: " << linesCount << std::endl);
    return;
  }

  Path *p = &lines[linesWritePos];
  std::vector<FLOAT_T> stepperStartPos(NUM_AXES, 0);
  std::vector<FLOAT_T> stepperEndPos(NUM_AXES, 0);
  FLOAT_T distance = 0;

  for (int axis = 0; axis < NUM_AXES; axis++) {
    stepperStartPos[axis] = round(startPos[axis] * axisStepsPerM[axis]);
    stepperEndPos[axis] = round(endPos[axis] * axisStepsPerM[axis]);
    axis_diff[axis] = (stepperEndPos[axis] - stepperStartPos[axis]) / axisStepsPerM[axis];
    //LOG("Axis " << axis << " length is " << axis_diff[axis] << std::endl);

    distance += axis_diff[axis] * axis_diff[axis];
  }

  distance = sqrt(distance);

  // Use the desired move time to calculate the machine-speed that matches the user's world-speed
  FLOAT_T machineSpeed = distance / desiredTime;

  p->initialize(stepperStartPos, stepperEndPos, distance, speed, accel, cancelable);

  if(p->isNoMove()){
    LOG( "PathPlanner::queueMove: Warning: no move path" << std::endl);
    PyEval_RestoreThread(_save);
    return; // No steps included
  }

  ////////////////////////////////////////////////////////////////////
  // PERFORM PLANNING
  ////////////////////////////////////////////////////////////////////

  p->calculate(axis_diff, minSpeeds, maxSpeeds, maxAccelerationStepsPerSquareSecond);
  updateTrapezoids();
  linesWritePos++;
  linesQueued++;
  linesCacheRemaining--;
  linesTicksQueued += p->getTimeInTicks();
  linesTicksRemaining -= p->getTimeInTicks();

  LOG("PathPlanner::queueMove: Move queued for the worker" << std::endl);

  if(linesWritePos>=moveCacheSize)
    linesWritePos = 0;

  // Notify the run() thread to work
  if((linesCacheRemaining == 0) || linesTicksRemaining <= 0){
    {
      std::lock_guard<std::mutex> lk(line_mutex);
      linesCount += linesQueued;
      linesTicksCount += linesTicksQueued;
    }
    linesQueued = 0;
    linesTicksQueued = 0;
    lineAvailable.notify_all();
    LOG("PathPlanner::queueMove: Poked the worker" << std::endl);
  }

  PyEval_RestoreThread(_save);
}


/**
   This is the path planner.
 
   It goes from the last entry and tries to increase the end speed of previous moves in a fashion that the maximum jerk
   is never exceeded. If a segment with reached maximum speed is met, the planner stops. Everything left from this
   is already optimal from previous updates.
   The first 2 entries in the queue are not checked. The first is the one that is already in print and the following will likely become active.
 
   The method is called before lines_count is increased!
*/
void PathPlanner::updateTrapezoids(){
  unsigned int first = linesWritePos;
  Path *firstLine;
  Path *act = &lines[linesWritePos];
  unsigned int maxfirst = linesPos; // first non fixed segment

  //LOG("UpdateTRapezoids:: "<<std::endl);
    
  // Search last fixed element
  while(first != maxfirst && !lines[first].isEndSpeedFixed()){
    //LOG("caling previousPlannerIndex"<<std::endl);
    previousPlannerIndex(first);
  }
  if(first != linesWritePos && lines[first].isEndSpeedFixed()){
    //LOG("caling nextPlannerIndex"<<std::endl);
    nextPlannerIndex(first);
  }
  if(first == linesWritePos){   // Nothing to plan
    //LOG("Nothing to plan"<<std::endl);
    act->block();
    act->setStartSpeedFixed(true);
    act->updateStepperPathParameters();
    act->unblock();
    return;
  }
  // now we have at least one additional move for optimization
  // that is not a wait move
  // First is now the new element or the first element with non fixed end speed.
  // anyhow, the start speed of first is fixed
  firstLine = &lines[first];
  firstLine->block(); // don't let printer touch this or following segments during update
  unsigned int previousIndex = linesWritePos;
  previousPlannerIndex(previousIndex);
  Path *previous = &lines[previousIndex];

  //LOG("UpdateTRapezoids:: computeMAxJunctionSpeed"<<std::endl);


  computeMaxJunctionSpeed(previous,act); // Set maximum junction speed if we have a real move before
  if(previous->isAxisOnlyMove(E_AXIS) != act->isAxisOnlyMove(E_AXIS)){
    previous->setEndSpeedFixed(true);
    act->setStartSpeedFixed(true);
    act->updateStepperPathParameters();
    firstLine->unblock();
    return;
  }
  backwardPlanner(linesWritePos,first);
  // Reduce speed to reachable speeds
  forwardPlanner(first);
	
  // Update precomputed data
  do{
    lines[first].updateStepperPathParameters();
    lines[first].unblock();  // Flying block to release next used segment as early as possible
    nextPlannerIndex(first);
    lines[first].block();
  }
  while(first!=linesWritePos);
  act->updateStepperPathParameters();
  act->unblock();

  //LOG("UpdateTRapezoids:: done"<<std::endl);
}

void PathPlanner::computeMaxJunctionSpeed(Path *previous, Path *current){
  FLOAT_T factor = 1;
    
  LOG("PathPlanner::computeMaxJunctionSpeed()"<<std::endl);

  for(int i=0; i<NUM_AXES; i++){
    FLOAT_T jerk = std::fabs(current->getSpeeds()[i] - previous->getSpeeds()[i]) * F_CPU; // m/tick * ticks/s = m/s

    if (jerk > maxJerks[i]){
      factor = std::min(factor, maxJerks[i] / jerk);
    }
  }

  previous->setMaxJunctionSpeed(std::min(previous->getFullSpeed() * factor, current->getFullSpeed()));
  LOG("PathPlanner::computeMaxJunctionSpeed: Max junction speed = "<<previous->getMaxJunctionSpeed()<<std::endl);
}

/**
   Compute the maximum speed from the last entered move.
   The backwards planner traverses the moves from last to first looking at deceleration. The RHS of the accelerate/decelerate ramp.
 
   start = last line inserted
   last = last element until we check
*/
void PathPlanner::backwardPlanner(unsigned int start, unsigned int last){
  Path *act = &lines[start],*previous;
  FLOAT_T lastJunctionSpeed = act->getEndSpeed(); // Start always with safe speed
	
  // Last element is already fixed in start speed
  while(start != last){
    previousPlannerIndex(start);
    previous = &lines[start];
		
    // Avoid speed calcs if we know we can accelerate within the line
    // acceleration is acceleration*distance*2! What can be reached if we try?
    lastJunctionSpeed = (act->willMoveReachFullSpeed() ? act->getFullSpeed() : sqrt(lastJunctionSpeed * lastJunctionSpeed + act->getAccelerationDistance2()));
    // If that speed is more that the maximum junction speed allowed then ...
    if(lastJunctionSpeed >= previous->getMaxJunctionSpeed()){   // Limit is reached
      // If the previous line's end speed has not been updated to maximum speed then do it now
      if(previous->getEndSpeed() != previous->getMaxJunctionSpeed()){
	previous->invalidateStepperPathParameters(); // Needs recomputation
	previous->setEndSpeed(std::max(previous->getMinSpeed(),previous->getMaxJunctionSpeed())); // possibly unneeded???
      }
      // If actual line start speed has not been updated to maximum speed then do it now
      if(act->getStartSpeed() != previous->getMaxJunctionSpeed()){
	act->setStartSpeed(std::max(act->getMinSpeed(),previous->getMaxJunctionSpeed())); // possibly unneeded???
	act->invalidateStepperPathParameters();
      }
      lastJunctionSpeed = previous->getEndSpeed();
    }
    else{
      // Block prev end and act start as calculated speed and recalculate plateau speeds (which could move the speed higher again)
      act->setStartSpeed(std::max(act->getMinSpeed(),lastJunctionSpeed));
      lastJunctionSpeed = std::max(lastJunctionSpeed,previous->getMinSpeed());
      previous->setEndSpeed(lastJunctionSpeed);
      previous->invalidateStepperPathParameters();
      act->invalidateStepperPathParameters();
    }
    act = previous;
  } // while loop
}

void PathPlanner::forwardPlanner(unsigned int first){
  Path *act;
  Path *next = &lines[first];
  FLOAT_T vmaxRight;
  FLOAT_T leftSpeed = next->getStartSpeed();
  while(first != linesWritePos){   // All except last segment, which has fixed end speed
    act = next;
    nextPlannerIndex(first);
    next = &lines[first];
		
    // Avoid speed calcs if we know we can accelerate within the line.
    vmaxRight = (act->willMoveReachFullSpeed() ? act->getFullSpeed() : sqrt(leftSpeed * leftSpeed + act->getAccelerationDistance2()));
    if(vmaxRight > act->getEndSpeed()){   // Could be higher next run?
      if(leftSpeed < act->getMinSpeed()){
	leftSpeed = act->getMinSpeed();
	act->setEndSpeed(sqrt(leftSpeed * leftSpeed + act->getAccelerationDistance2()));
      }
      act->setStartSpeed(leftSpeed);

      leftSpeed = std::max(std::min(act->getEndSpeed(),act->getMaxJunctionSpeed()),next->getMinSpeed());
      next->setStartSpeed(leftSpeed);
      if(act->getEndSpeed() == act->getMaxJunctionSpeed()){  // Full speed reached, don't compute again!            
	act->setEndSpeedFixed(true);
	next->setStartSpeedFixed(true);
      }
      act->invalidateStepperPathParameters();
    }
    else{     // We can accelerate full speed without reaching limit, which is as fast as possible. Fix it!
      act->fixStartAndEndSpeed();
      act->invalidateStepperPathParameters();
      if(act->getMinSpeed() > leftSpeed){
	leftSpeed = act->getMinSpeed();
	vmaxRight = sqrt(leftSpeed * leftSpeed + act->getAccelerationDistance2());
      }
      act->setStartSpeed(leftSpeed);
      act->setEndSpeed(std::max(act->getMinSpeed(), vmaxRight));

      leftSpeed = std::max(std::min(act->getEndSpeed(), act->getMaxJunctionSpeed()), next->getMinSpeed());
      next->setStartSpeed(leftSpeed);
      next->setStartSpeedFixed(true);
    }
  }
  next->setStartSpeed(std::max(next->getMinSpeed(), leftSpeed)); // This is the new segment, which is updated anyway, no extra flag needed.
}

void PathPlanner::runThread() {
  stop=false;
  LOG("PathPlanner: starting thread" << std::endl);
  pru.runThread();	
  runningThread = std::thread([this]() {
      this->run();
    });
}

void PathPlanner::stopThread(bool join) {
  Py_BEGIN_ALLOW_THREADS
    pru.stopThread(join);	
  stop=true;
  lineAvailable.notify_all();
  if(join && runningThread.joinable()) {
    runningThread.join();
  }
  Py_END_ALLOW_THREADS
    }

PathPlanner::~PathPlanner() {
  if(runningThread.joinable()) {
    stopThread(true);
  }
}

void PathPlanner::waitUntilFinished() {
  Py_BEGIN_ALLOW_THREADS    
    std::unique_lock<std::mutex> lk(line_mutex);
  lineAvailable.wait(lk, [this]{
      return linesCount==0 || stop;
    });
	
  //Wait for PruTimer then
  if(!stop) {
    pru.waitUntilFinished();
  }
  Py_END_ALLOW_THREADS
    }

void PathPlanner::reset() {
  pru.reset();
}

void PathPlanner::run() {
  bool waitUntilFilledUp = true;
  LOG("PathPLanner::run(): loop starting" << std::endl);
	
  while(!stop) {		
    std::unique_lock<std::mutex> lk(line_mutex);		
    lineAvailable.wait(lk, [this]{return linesCount>0 || stop;});		
    Path* cur = &lines[linesPos];
    assert(cur);
    std::vector<SteppersCommand> commands(cur->getPrimaryAxisSteps());
    std::vector<int> error = cur->getInitialErrors();

    // If the buffer is half or more empty and the line to print is an optimized one, 
    // wait for 500 ms again so that we can get some other path in the path planner buffer, 
    // and we do that until the buffer is not anymore half empty.
    if(!isLinesBufferFilled() && cur->getTimeInTicks() > 0 && waitUntilFilledUp) {
      unsigned lastCount = 0;
      LOG("PathPLanner::run(): Waiting for buffer to fill up. " << linesCount  << " lines pending, lastCount is " << lastCount << std::endl);
      do {
	lastCount = linesCount;				
	lineAvailable.wait_for(lk,  std::chrono::milliseconds(printMoveBufferWait), [this,lastCount]{
	    return linesCount>lastCount || stop;
	  });				
      } while(lastCount<linesCount && linesCount<moveCacheSize && !stop);
      LOG("PathPLanner::run(): Done waiting for buffer to fill up... " << linesCount  << " lines ready. " << lastCount << std::endl);			
      waitUntilFilledUp = false;
    }
		
    //The buffer is empty, we enable again the "wait until buffer is enough full" timing procedure.
    if(linesCount<=1) {
      waitUntilFilledUp = true;
      LOG("PathPLanner::run(): ### Move Command Buffer Empty ###" << std::endl);
    }
		
    lk.unlock();
		
    if(!linesCount || stop){
      continue;
    }
		
    long cur_errupd = 0;
    int directionMask = 0;      //0bCBAHEZYX
    int cancellableMask = 0;
    unsigned int vMaxReached;
    unsigned int timer_accel = 0;
    unsigned int timer_decel = 0;
    unsigned int interval = 0;
		
    if(cur->isBlocked()){   // This step is in computation - shouldn't happen
      cur = NULL;
      LOG( "PathPLanner::run():  thread: path " <<  std::dec << linesPos<< " is blocked, waiting... " << std::endl);
      std::this_thread::sleep_for( std::chrono::milliseconds(100) );
      continue;
    }
		
    // Only enable axes that are moving. If the axis doesn't need to move then it can stay disabled depending on configuration.
    cur->fixStartAndEndSpeed();
    cur_errupd = cur->getDeltas()[cur->getPrimaryAxis()];
    if(!cur->areParameterUpToDate()){  // should never happen, but with bad timings???
      LOG("PathPLanner::run(): Path planner thread: Need to update paramters! This should not happen!" << std::endl);
      cur->updateStepperPathParameters();
    }

    StepperPathParameters stepperPath = cur->getStepperPathParameters();
    unsigned long long fPrimaryAxisAcceleration = 262144.0 * cur->getPrimaryAxisAcceleration() / F_CPU; // (2^18)
		
    vMaxReached = stepperPath.vStart;

    directionMask = 0;
    cancellableMask = 0;
    for(int i=0; i<NUM_AXES; i++){
      //LOG("Direction for axis " << i << " is " << cur->isAxisPositiveMove(i) << std::endl);
      directionMask |= (cur->isAxisPositiveMove(i) << i);
    }
    if(cur->isCancelable()) {
      for(int i=0; i<NUM_AXES; i++)
	cancellableMask |= (cur->isAxisMove(i) << i);
    }		
    LOG("PathPLanner::run(): Direction mask: " << directionMask << std::endl);
    LOG("PathPLanner::run(): Cancel    mask: " << cancellableMask << std::endl);
    LOG("PathPLanner::run(): startSpeed:   " << cur->getStartSpeed() << std::endl);
    LOG("PathPLanner::run(): fullSpeed:    " << cur->getFullSpeed() << std::endl);
    LOG("PathPLanner::run(): endSpeed:     " << cur->getEndSpeed() << std::endl);
    LOG("PathPLanner::run(): acceleration: " << cur->getAcceleration() << std::endl);
    LOG("PathPLanner::run(): accelTime:    " << ((cur->getFullSpeed() - cur->getStartSpeed())/cur->getAcceleration()) << std::endl);
        
        

    for(unsigned int stepNumber=0; stepNumber<cur->getPrimaryAxisSteps(); stepNumber++){
      SteppersCommand& cmd = commands.at(stepNumber);
      cmd.direction = (uint8_t) directionMask;
      cmd.cancellableMask = (uint8_t) cancellableMask;
			
      if((stepNumber == cur->getPrimaryAxisSteps() - 1) && cur->isSyncEvent()){
	if(cur->isSyncWaitEvent())
	  cmd.options = STEPPER_COMMAND_OPTION_SYNCWAIT_EVENT;
	else
	  cmd.options = STEPPER_COMMAND_OPTION_SYNC_EVENT;
      }
      else 
	cmd.options = 0;

      //LOG( "Doing step " << stepNumber << " of "<<cur->getPrimaryAxisSteps() <<std::endl);

      cmd.step = 0;
      for(int i=0; i<NUM_AXES; i++){
	if(cur->isAxisMove(i)){
	  if((error[i] -= cur->getDeltas()[i]) < 0){
	    cmd.step |= (1 << i);
	    error[i] += cur_errupd;
	  }
	}
      }

      //If acceleration is enabled on this move and we are in the acceleration segment, calculate the current interval
      if (stepNumber <= stepperPath.accelSteps){   // we are accelerating
	//LOG( "Acceleration" << std::endl);
	vMaxReached = ComputeV(timer_accel, fPrimaryAxisAcceleration) + stepperPath.vStart;
	if(vMaxReached>stepperPath.vMax)
	  vMaxReached = stepperPath.vMax;
	unsigned long v = vMaxReached;
	if (v > 0)
	  interval = F_CPU/(v);
	timer_accel+=interval;
      }
      else if (cur->getPrimaryAxisSteps() - stepNumber <= stepperPath.decelSteps){     // time to slow down
	//LOG( "Decelleration "<<std::endl);
	unsigned long v = ComputeV(timer_decel, fPrimaryAxisAcceleration);
	if (v > vMaxReached)   // if deceleration goes too far it can become too large
	  v = stepperPath.vEnd;
	else{
	  v=vMaxReached - v;
	  if (v < stepperPath.vEnd)
	    v = stepperPath.vEnd; // extra steps at the end of desceleration due to rounding erros
	}
	if (v > 0)
	  interval = F_CPU/(v);
	timer_decel += interval;
      }
      else{ // full speed reached
	//LOG( "Cruising "<<std::endl);
	interval = cur->getFullInterval();
      }

      //LOG("Interval: " << interval << std::endl);
      assert(interval < F_CPU*4);
      cmd.delay = (uint32_t)interval;
    }
		

    //LOG("Current move time " << pru.getTotalQueuedMovesTime() / (double) F_CPU << std::endl);
		
    //Wait until we need to push some lines so that the path planner can fill up
    pru.waitUntilLowMoveTime((F_CPU/1000)*minBufferedMoveTime); //in seconds
		
    LOG( "PathPLanner::run(): Sending " << std::dec << linesPos << ", Start speed=" << cur->getStartSpeed() << ", end speed="<<cur->getEndSpeed() << ", nb steps = " << cur->getPrimaryAxisSteps() << std::endl);
		
    pru.push_block((uint8_t*)commands.data(), sizeof(SteppersCommand)*cur->getPrimaryAxisSteps(), sizeof(SteppersCommand), linesPos, cur->getTimeInTicks());
    LOG( "PathPLanner::run(): Done sending with " << std::dec << linesPos << std::endl);
		
    removeCurrentLine();
    lineAvailable.notify_all();
  }
}

std::vector<FLOAT_T> PathPlanner::getState()
{
  return state;
}
