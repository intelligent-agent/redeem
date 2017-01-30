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
  LOG( "PathPlanner " << std::endl);
  moveCacheSize = cacheSize;
  lines.resize(moveCacheSize);
  printMoveBufferWait = 250;
  maxBufferedMoveTime = 6 * printMoveBufferWait;
  linesCount = 0;
  linesTicksCount = 0;
  stop = false;
  hasEndABC = false;
	
  max_path_length = 1e6;
  axis_config = AXIS_CONFIG_XY;
  has_slaves = false;

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

void PathPlanner::queueMove(VectorN startPos, VectorN endPos,
			    FLOAT_T speed, FLOAT_T accel, 
			    bool cancelable, bool optimize, 
			    bool enable_soft_endstops, bool use_bed_matrix, 
			    bool use_backlash_compensation, int tool_axis,
			    bool virgin) 
{
  ////////////////////////////////////////////////////////////////////
  // PRE-PROCESSING
  ////////////////////////////////////////////////////////////////////
	
  LOG("NEW MOVE:\n");
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
    
  VectorN vec = endPos - state;
  
  for (size_t i = 0; i< NUM_AXES; ++i) {
    assert(!std::isnan(vec[i]));
    assert(!std::isnan(endPos[i]));
    assert(!std::isnan(state[i]));
  }

  LOG("startPos: " << startPos[0] << " " << startPos[1] << " " << startPos[2] << std::endl);
  LOG("state: " << state[0] << " " << state[1] << " " << state[2] << std::endl);
  LOG("vec before: " << vec[0] << " " << vec[1] << " " << vec[2] << std::endl);
	
  // Check if the path needs to be split
  if( splitInput(state, vec, speed, accel, cancelable, optimize, use_backlash_compensation, tool_axis, virgin) ) {
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
  VectorN delta;
  FLOAT_T sum_delta = 0.0;
  for (int i = 0; i<NUM_AXES; ++i) {
    assert(!std::isnan(vec[i]));
    num_steps = round(fabs(vec[i])*axisStepsPerM[i]);
    delta[i] = sgn(vec[i])*num_steps/axisStepsPerM[i];
    vec[i] = delta[i];
    sum_delta += fabs(delta[i]);
  }


  // check for a no-move
  if (sum_delta == 0.0) {
    LOG("no move" << std::endl);
    return;
  }
	
  // 'vec' now contains the actual distance travelled, by the motors, 
  // after taking into account the discrete nature of the stepper motors
	
  reverseTransformVector(vec);
	
  // and now vec is back in physical space
  LOG("vec after: " << vec[0] << " " << vec[1] << " " << vec[2] << std::endl);
	
  // backlash compensation
  if (use_backlash_compensation) {
    backlashCompensation(delta);
  }

  // change startPos and endPos to give the change in position using machine coordinates
  // also update the state of the machine, i.e. where the effector really is in physical space
  startPos = state; // the real starting position
  endPos = state + delta; // the real ending position
  state += vec; // update the new state of the machine

  LOG("new state: " << state[0] << " " << state[1] << " " << state[2] << std::endl);
    
  // handle any slaving activity
  handleSlaves(startPos, endPos);

  // LOG("MOVE COMMAND:\n");
  // for (int i = 0; i<NUM_AXES; ++i) {
  //   LOG("AXIS " << i << ": start = " << startPos[i] << ", end = " << state[i] << "\n");
  // }
    	
  ////////////////////////////////////////////////////////////////////
  // LOAD INTO QUEUE
  ////////////////////////////////////////////////////////////////////
    
    
  VectorN axis_diff;        // Axis movement in m
  PyThreadState *_save; 
  _save = PyEval_SaveThread();

  unsigned int linesCacheRemaining = moveCacheSize - linesCount;
  long long linesTicksRemaining = maxBufferedMoveTime - linesTicksCount;

  // wait for the worker
  if(!doesPathQueueHaveSpace()){
    std::unique_lock<std::mutex> lk(line_mutex);
    QUEUELOG( "Waiting for free move command space... Current: " << moveCacheSize - linesCount << " lines that take " << linesTicksCount << " ticks"  << std::endl);
    pathQueueHasSpace.wait(lk, [this] { return this->doesPathQueueHaveSpace(); });
    linesCacheRemaining = moveCacheSize - linesCount;
    linesTicksRemaining = maxBufferedMoveTime - linesTicksCount;
  }	
  if(stop){
    PyEval_RestoreThread(_save);
    LOG( "Stopped/aborted/Cancelled while waiting for free move command space. linesCount: " << linesCount << std::endl);
    return;
  }

  Path *p = &lines[linesWritePos];
  VectorN stepperStartPos;
  VectorN stepperEndPos;
  FLOAT_T distance = 0;

  for (int axis = 0; axis < NUM_AXES; axis++) {
    stepperStartPos[axis] = round(startPos[axis] * axisStepsPerM[axis]);
    stepperEndPos[axis] = round(endPos[axis] * axisStepsPerM[axis]);
    axis_diff[axis] = (stepperEndPos[axis] - stepperStartPos[axis]) / axisStepsPerM[axis];
    LOG("Axis " << axis << " length is " << axis_diff[axis] << " from " << stepperStartPos[axis] << " to " << stepperEndPos[axis] << std::endl);

    distance += axis_diff[axis] * axis_diff[axis];
  }

  distance = sqrt(distance);

  // Use the desired move time to calculate the machine-speed that matches the user's world-speed
  FLOAT_T machineSpeed = distance / desiredTime;

  p->initialize(stepperStartPos, stepperEndPos, distance, cancelable);

  if(p->isNoMove()){
    LOG( "Warning: no move path" << std::endl);
    PyEval_RestoreThread(_save);
    return; // No steps included
  }

  ////////////////////////////////////////////////////////////////////
  // PERFORM PLANNING
  ////////////////////////////////////////////////////////////////////

  p->calculate(axis_diff, minSpeeds, maxSpeeds, maxAccelerationStepsPerSquareSecond, machineSpeed, accel);
  updateTrapezoids();
  linesWritePos++;
  linesCacheRemaining--;
  linesTicksRemaining -= p->getTimeInTicks();

  QUEUELOG("Move queued for the worker" << std::endl);

  if(linesWritePos>=moveCacheSize)
    linesWritePos = 0;

  // Notify the run() thread to work
  if((linesCacheRemaining == 0) || linesTicksRemaining <= 0){
    {
      std::lock_guard<std::mutex> lk(line_mutex);
      linesCount++;
      linesTicksCount += p->getTimeInTicks();
    }
    notifyIfPathQueueIsReadyToPrint();
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
    first = previousPlannerIndex(first);
  }
  if(first != linesWritePos && lines[first].isEndSpeedFixed()){
    //LOG("caling nextPlannerIndex"<<std::endl);
    first = nextPlannerIndex(first);
  }
  if(first == linesWritePos){   // Nothing to plan
    //LOG("Nothing to plan"<<std::endl);
    act->block();
    act->setStartSpeedFixed(true);
    act->unblock();
    return;
  }
  // now we have at least one additional move for optimization
  // that is not a wait move
  // First is now the new element or the first element with non fixed end speed.
  // anyhow, the start speed of first is fixed
  firstLine = &lines[first];
  firstLine->block(); // don't let printer touch this or following segments during update
  unsigned int previousIndex = previousPlannerIndex(linesWritePos);
  Path *previous = &lines[previousIndex];

  //LOG("UpdateTRapezoids:: computeMAxJunctionSpeed"<<std::endl);


  computeMaxJunctionSpeed(previous,act); // Set maximum junction speed if we have a real move before
  if((previous->getAxisMoveMask() & act->getAxisMoveMask()) == 0){ // if no axes move in both moves, there's nothing to optimize
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
    lines[first].unblock();  // Flying block to release next used segment as early as possible
    first = nextPlannerIndex(first);
    lines[first].block();
  }
  while(first!=linesWritePos);
  act->unblock();

  //LOG("UpdateTRapezoids:: done"<<std::endl);
}

void PathPlanner::computeMaxJunctionSpeed(Path *previous, Path *current){
  FLOAT_T factor = 1;
    
  LOG("Computing Max junction speed"<<std::endl);

  for(int i=0; i<NUM_AXES; i++){
    FLOAT_T jerk = std::fabs(current->getSpeeds()[i] - previous->getSpeeds()[i]) / axisStepsPerM[i]; // steps/s / steps/m = m/s

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
    start = previousPlannerIndex(start);
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
    first = nextPlannerIndex(first);
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
  stop = true;
  notifyIfPathQueueIsReadyToPrint();

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
  pathQueueHasSpace.wait(lk, [this] { return linesCount==0 || stop; });
	
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
  LOG("PathPlanner loop starting" << std::endl);

  const unsigned int maxCommandsPerBlock = pru.getMaxBytesPerBlock() / sizeof(SteppersCommand);
  std::unique_ptr<SteppersCommand[]> commandBlock(new SteppersCommand[maxCommandsPerBlock]);
	
  while(!stop) {		
    std::unique_lock<std::mutex> lk(line_mutex);
    if (!isPathQueueReadyToPrint()) {
      pathQueueReadyToPrint.wait(lk, [this] { return this->isPathQueueReadyToPrint(); });
    }
    Path* cur = &lines[linesPos];

    // If the buffer is half or more empty and the line to print is an optimized one, 
    // wait for 500 ms again so that we can get some other path in the path planner buffer, 
    // and we do that until the buffer is not anymore half empty.
    if(waitUntilFilledUp && !isLinesBufferFilled() && cur->getTimeInTicks() > 0) {
      unsigned lastCount = 0;
      QUEUELOG("Waiting for buffer to fill up. " << linesCount  << " lines pending, lastCount is " << lastCount << std::endl);
      do {
	lastCount = linesCount;
	if (lastCount == 0) { // if there are no lines in the queue, we can wait indefinitely
	  pathQueueReadyToPrint.wait(lk, [this, lastCount] { return linesCount > lastCount || stop; });
	}
	else { // if there are lines in the queue, we need to cap the wait at printMoveBufferWait
	  pathQueueReadyToPrint.wait_for(lk, std::chrono::milliseconds(printMoveBufferWait), [this, lastCount] {
	    return linesCount > lastCount || stop;
	  });
	}
      } while(lastCount<linesCount && linesCount<moveCacheSize && !stop);
      QUEUELOG("Done waiting for buffer to fill up... " << linesCount  << " lines ready. " << lastCount << std::endl);			
      waitUntilFilledUp = false;
    }
		
    //The buffer is empty, we enable again the "wait until buffer is enough full" timing procedure.
    if(linesCount<=1) {
      waitUntilFilledUp = true;
      QUEUELOG("### Move Command Buffer Empty ###" << std::endl);
    }

    lk.unlock();

    if(!linesCount || stop){
      continue;
    }

    if(cur->isBlocked()){   // This step is in computation - shouldn't happen
      cur = NULL;
      QUEUELOG( "Path planner thread: path " <<  std::dec << linesPos<< " is blocked, waiting... " << std::endl);
      std::this_thread::sleep_for( std::chrono::milliseconds(100) );
      continue;
    }
		
    // Only enable axes that are moving. If the axis doesn't need to move then it can stay disabled depending on configuration.
    cur->fixStartAndEndSpeed();
    if(!cur->areParameterUpToDate()){  // should never happen, but with bad timings???
      LOG( "Path planner thread: Need to update paramters! This should not happen!" << std::endl);
      cur->updateStepperPathParameters();
    }

    StepperPathParameters stepperPath = cur->getStepperPathParameters();

    int moveMask = 0;
    int directionMask = 0;
    int cancellableMask = 0;
    for(int i=0; i<NUM_AXES; i++){
      LOG("Direction for axis " << i << " is " << cur->isAxisPositiveMove(i) << std::endl);
      moveMask |= (cur->isAxisMove(i) << i);
      directionMask |= (cur->isAxisPositiveMove(i) << i);
    }

    if(cur->isCancelable()) {
      for(int i=0; i<NUM_AXES; i++)
	cancellableMask |= (cur->isAxisMove(i) << i);
    }

    LOG("Direction mask: " << directionMask << std::endl);
    LOG("Cancel    mask: " << cancellableMask << std::endl);

    LOG("startSpeed:   " << cur->getStartSpeed() << std::endl);
    LOG("fullSpeed:    " << cur->getFullSpeed() << std::endl);
    LOG("acceleration: " << cur->getAcceleration() << std::endl);
    LOG("accelTime:    " << stepperPath.accelTime << std::endl);
    LOG("cruiseTime:    " << stepperPath.cruiseTime << std::endl);
    LOG("decelTime:    " << stepperPath.decelTime << std::endl);

    LOG("Sending " << std::dec << linesPos << ", Start speed=" << cur->getStartSpeed() << ", end speed=" << cur->getEndSpeed() << std::endl);

    runMove(moveMask, cancellableMask, cur->isSyncEvent(), cur->isSyncWaitEvent(), stepperPath, commandBlock, maxCommandsPerBlock);

    //LOG("Current move time " << pru.getTotalQueuedMovesTime() / (double) F_CPU << std::endl);

    LOG( "Done sending with " << std::dec << linesPos << std::endl);
		
    removeCurrentLine();
    notifyIfPathQueueHasSpace();
  }
}

void PathPlanner::runMove(
  const int moveMask,
  const int cancellableMask,
  const bool sync,
  const bool wait,
  const StepperPathParameters& params,
  std::unique_ptr<SteppersCommand[]> const &commands,
  const size_t commandsLength) {


  struct Step {
    int axis;
    int number;
    FLOAT_T time;
    unsigned long long roundedTime;

    Step(int axis, int number, FLOAT_T time)
      : axis(axis),
      number(number),
      time(time),
      roundedTime(std::llround(time / 2000.0) * 2000)
    {}

    bool operator >(Step const& o) const {
      return roundedTime > o.roundedTime;
    }
  };

  std::priority_queue < Step, std::vector<Step>, std::greater<Step>> steps;
  std::vector<StepperPath> stepperPaths(NUM_AXES);
  std::vector<StepperPathState> stepperPathStates(NUM_AXES);
  std::vector<unsigned long long> finalStepTimes(NUM_AXES, 0);
  unsigned long long finalTime = 0;
  size_t commandsIndex = 0;

  for (int i = 0; i < NUM_AXES; i++) {
    if (moveMask & (1 << i)) {
      stepperPaths[i] = StepperPath(params, i);
      assert(stepperPaths[i].getNumSteps() != 0);
      stepperPathStates[i] = stepperPaths[i].calculateNextStep(stepperPathStates[i], 0, 0.5);
      LOG("axis " << i << " " << stepperPaths[i].toString() << std::endl);
      steps.push(Step(i, 0, stepperPathStates[i].lastStepTime * F_CPU_FLOAT));
    }
  }

  for (size_t i = 0; i < commandsLength; i++) {
    commands[i] = {};
  }

  LOG("accel time: " << params.accelTime << " cruise time: " << params.cruiseTime << " decel time: " << params.decelTime << std::endl);

  while (!steps.empty()) {
    SteppersCommand& cmd = commands[commandsIndex];
    
    cmd.cancellableMask = cancellableMask;

    //LOG("time: " << time << std::endl;)
    const unsigned long long time = steps.top().roundedTime;

    // Step what needs to be stepped
    while (!steps.empty() && steps.top().roundedTime <= time) {
      const Step step = steps.top();

      assert(!(cmd.step & (1 << step.axis))); // we should never double-step in a single command

      steps.pop();

      auto direction = stepperPaths[step.axis].stepDirection(stepperPathStates[step.axis]);
      if (direction != StepDirection::None) {
	cmd.step |= 1 << step.axis;

	if (direction == StepDirection::Forward) {
	  cmd.direction |= 1 << step.axis;
	}
      }

      if (step.number + 1 != stepperPaths[step.axis].getNumSteps()) {
	stepperPathStates[step.axis] = stepperPaths[step.axis].calculateNextStep(stepperPathStates[step.axis], step.number + 0.5, 1.0);

	Step nextStep(step.axis, step.number + 1, stepperPathStates[step.axis].lastStepTime * F_CPU_FLOAT);
	if (nextStep.roundedTime <= time) {
	  LOG("needed a double step for axis " << nextStep.axis << " at times "
	    << (unsigned long long)step.time << " and " << (unsigned long long)nextStep.time
	    << " and step number " << nextStep.number << std::endl);
	  LOG("time is " << time << std::endl);
	  assert(0);
	}

	assert(nextStep.time - step.time < F_CPU_FLOAT);

	steps.push(nextStep);
      }
      else {
	stepperPathStates[step.axis] = stepperPaths[step.axis].calculateNextStep(stepperPathStates[step.axis], step.number + 0.5, 0.5);

	assert(stepperPaths[step.axis].isInFinalPhase(stepperPathStates[step.axis], step.number + 1.0));
	FLOAT_T finalAxisStepTime = stepperPathStates[step.axis].lastStepTime;

	stepperPathStates[step.axis] = stepperPaths[step.axis].calculateNextStep(stepperPathStates[step.axis], step.number + 1.0, 0.50);

	assert(std::isfinite(finalAxisStepTime));
	finalStepTimes[step.axis] = std::llround(finalAxisStepTime * F_CPU_FLOAT);
	finalTime = std::max(finalTime, finalStepTimes[step.axis]);
	assert(finalStepTimes[step.axis] > time);

	LOG("lastStepTime: " << finalAxisStepTime << " move time: " << params.accelTime + params.cruiseTime + params.decelTime
	  << " accelTime: " << params.accelTime << " cruiseTime: " << params.cruiseTime << " decelTime " << params.decelTime
	  << " error: " << finalAxisStepTime - (params.accelTime + params.cruiseTime + params.decelTime) << std::endl);

	LOG("error after jumping to end: " << stepperPathStates[step.axis].lastStepTime - (params.accelTime + params.cruiseTime + params.decelTime) << std::endl);

	assert(std::abs(finalAxisStepTime - (params.accelTime + params.cruiseTime + params.decelTime)) < 10 * CPU_CYCLE_LENGTH);
      }
    }

    if (!steps.empty()) {
      assert(steps.top().roundedTime > time);
      cmd.delay = steps.top().roundedTime - time;
    }
    else {
      assert(finalTime > time);
      cmd.delay = finalTime - time;
      cmd.delay += 2000 - cmd.delay % 2000;
    }

    assert(cmd.delay >= 2000);
    assert(cmd.delay < F_CPU);

    commandsIndex++;

    if (commandsIndex == commandsLength) {
      pru.push_block((uint8_t*)&commands[0], sizeof(SteppersCommand)*commandsIndex, sizeof(SteppersCommand), commandsIndex);
      commandsIndex = 0;

      for (size_t i = 0; i < commandsLength; i++) {
	commands[i] = {};
      }
    }
  }

  if (sync) {
    if (commandsIndex == 0) {
      commandsIndex = 1;
      assert(commandsIndex < commandsLength);
      assert(commands[commandsIndex].step == 0 && commands[commandsIndex].delay == 0);
    }

    assert(commandsIndex > 0 && commandsIndex <= commandsLength);

    SteppersCommand& cmd = commands[commandsIndex - 1];
    if (wait) cmd.options = STEPPER_COMMAND_OPTION_SYNCWAIT_EVENT;
    else cmd.options = STEPPER_COMMAND_OPTION_SYNC_EVENT;
  }

  if (commandsIndex != 0) {
    pru.push_block((uint8_t*)&commands[0], sizeof(SteppersCommand)*commandsIndex, sizeof(SteppersCommand), commandsIndex);
  }

  {
    unsigned long long earliestFinishTime = ULLONG_MAX;
    unsigned long long latestFinishTime = 0;
    for (int i = 0; i < NUM_AXES; i++) {

      if (moveMask & (1 << i)) {
	LOG("axis " << i << " finished at " << finalStepTimes[i] << std::endl);
	if (finalStepTimes[i] != 0) {
	  earliestFinishTime = std::min(earliestFinishTime, finalStepTimes[i]);
	  latestFinishTime = std::max(latestFinishTime, finalStepTimes[i]);
	}
      }
    }
    LOG("finish times ranged from " << earliestFinishTime << " to " << latestFinishTime << ", which is "
      << latestFinishTime - earliestFinishTime << " ticks or " << (latestFinishTime - earliestFinishTime) / F_CPU_FLOAT << " seconds"
      << std::endl);
    assert((latestFinishTime - earliestFinishTime) / F_CPU_FLOAT < 10 * CPU_CYCLE_LENGTH); // all axes should finish within 10 PRU cycles
  }

  assert(steps.empty());
}

VectorN PathPlanner::getState()
{
  return state;
}
