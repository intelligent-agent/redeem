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
#include <array>
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
	
  axis_config = AXIS_CONFIG_XY;
  has_slaves = false;

  // set bed compensation matrix to identity
  matrix_bed_comp.resize(9, 0);
  matrix_bed_comp[0] = 1.0;
  matrix_bed_comp[4] = 1.0;
  matrix_bed_comp[8] = 1.0;

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

void PathPlanner::queueMove(VectorN endWorldPos,
			    FLOAT_T speed, FLOAT_T accel, 
			    bool cancelable, bool optimize, 
			    bool enable_soft_endstops, bool use_bed_matrix, 
			    bool use_backlash_compensation, int tool_axis) 
{
  ////////////////////////////////////////////////////////////////////
  // PRE-PROCESSING
  ////////////////////////////////////////////////////////////////////
	
  LOG("NEW MOVE:\n");
  // for (int i = 0; i<NUM_AXES; ++i) {
  //   LOG("AXIS " << i << ": start = " << startPos[i] << "(" << state[i] << "), end = " << endPos[i] << "\n");
  // }

  VectorN startWorldPos = getState();

  // Cap the end position based on soft end stops
  if (enable_soft_endstops) {
    if (softEndStopApply(endWorldPos)) {
      return;
    }
  }
  // Calculate the position to reach, with bed levelling
  if (use_bed_matrix) {
    LOG("Before matrix X: "<< endWorldPos[0]<<" Y: "<< endWorldPos[1]<<" Z: "<< endWorldPos[2]<<"\n");
    applyBedCompensation(endWorldPos);
    LOG("After matrix X: "<< endWorldPos[0]<<" Y: "<< endWorldPos[1]<<" Z: "<< endWorldPos[2]<<"\n");
  }

  // handle any slaving activity
  handleSlaves(startWorldPos, endWorldPos);
	
  // Get the vector to move us from where we are, to where we ideally want to be.
  IntVectorN endPos = (endWorldPos * axisStepsPerM).round();

  // First convert to machine-space
  switch (axis_config)
  {
  case AXIS_CONFIG_DELTA:
  {
    const Vector3 deltaEnd = delta_bot.worldToDelta(endWorldPos.toVector3());
    LOG("Delta end: X: " << deltaEnd[0] << " Y: " << deltaEnd[1] << " Z: " << deltaEnd[2] << std::endl);
    const IntVector3 endMotionPos = (deltaEnd * axisStepsPerM.toVector3()).round();
    LOG("Delta end motors: X: " << endMotionPos[0] << " Y: " << endMotionPos[1] << " Z: " << endMotionPos[2] << std::endl);
    endPos[0] = endMotionPos[0];
    endPos[1] = endMotionPos[1];
    endPos[2] = endMotionPos[2];
    break;
  }
  case AXIS_CONFIG_CORE_XY:
  {
    const Vector3 coreXYEnd = worldToCoreXY(endWorldPos.toVector3());
    const IntVector3 endMotionPos = (coreXYEnd * axisStepsPerM.toVector3()).round();

    endPos[0] = endMotionPos[0];
    endPos[1] = endMotionPos[1];
    assert(endPos[2] == endMotionPos[2]);
    endPos[2] = endMotionPos[2];
    break;
  }
  case AXIS_CONFIG_H_BELT:
  {
    const Vector3 hBeltEnd = worldToHBelt(endWorldPos.toVector3());
    const IntVector3 endMotionPos = (hBeltEnd * axisStepsPerM.toVector3()).round();

    endPos[0] = endMotionPos[0];
    endPos[1] = endMotionPos[1];
    assert(endPos[2] == endMotionPos[2]);
    endPos[2] = endMotionPos[2];
    break;
  }
  case AXIS_CONFIG_XY:
  break;
  default:
    endPos.zero();
    LOG("don't know what to do for axis config: " << axis_config << std::endl);
    assert(0);
    break;
  }

  // This is only useful for debugging purposes - the motion platform may not move
  // directly from start to end, but the net total of steps should equal this.
  const IntVectorN rawDeltas = endPos - state;

  LOG("startWorldPos (m): " << startWorldPos[0] << " " << startWorldPos[1] << " " << startWorldPos[2] << std::endl);
  LOG("endWorldPos (m): " << endWorldPos[0] << " " << endWorldPos[1] << " " << endWorldPos[2] << std::endl);
  LOG("state (steps): " << state[0] << " " << state[1] << " " << state[2] << std::endl);
  LOG("endPos (steps): " << endPos[0] << " " << endPos[1] << " " << endPos[2] << std::endl);
  LOG("rawDeltas: " << rawDeltas[0] << " " << rawDeltas[1] << " " << rawDeltas[2] << std::endl);

  bool move = false;

  for (int i = 0; i < NUM_AXES; i++) {
    if (rawDeltas[i] != 0)
    {
      move = true;
      break;
    }
  }

  // check for a no-move
  if (!move) {
    LOG("no move" << std::endl);
    return;
  }

  IntVectorN tweakedEndPos = endPos;

  // backlash compensation
  if (use_backlash_compensation) {
    IntVectorN adjustedDeltas = rawDeltas;
    backlashCompensation(adjustedDeltas);

    tweakedEndPos = state + adjustedDeltas;
  }

  ////////////////////////////////////////////////////////////////////
  // LOAD INTO QUEUE
  ////////////////////////////////////////////////////////////////////
  
  PyThreadState *_save; 
  _save = PyEval_SaveThread();

  Path p;

  p.initialize(state, tweakedEndPos, startWorldPos, endWorldPos, axisStepsPerM,
    minSpeeds, maxSpeeds, maxAccelerationMPerSquareSecond,
    speed, accel, axis_config, delta_bot, cancelable);

  if (p.isNoMove()) {
    LOG("Warning: no move path" << std::endl);
    assert(0); /// TODO We should have bailed before now
    PyEval_RestoreThread(_save);
    return; // No steps included
  }

  LOG("checking deltas...");
  std::cout.flush();
  {
    IntVectorN realDeltas;

    for (const auto& axisSteps : p.getSteps())
    {
      FLOAT_T lastTime = 0;
      for (const auto& step : axisSteps)
      {
        realDeltas[step.axis] += step.direction ? 1 : -1;
	assert(step.time > lastTime);
	lastTime = step.time;
      }
    }

    for (int i = 0; i < NUM_AXES; i++)
    {
      if (state[i] + realDeltas[i] != endPos[i])
      {
	LOG("step count sanity check failed on axis " << i << " because " << state[i] << " + " << realDeltas[i] << " != " << endPos[i] << std::endl);
	assert(0);
      }
    }
  }
  LOG("done!" << std::endl);

  unsigned int linesCacheRemaining = moveCacheSize - linesCount;
  long long linesTicksRemaining = maxBufferedMoveTime - linesTicksCount;

  // wait for the worker
  if(!doesPathQueueHaveSpace()){
    std::unique_lock<std::mutex> lk(line_mutex);
    QUEUELOG( "Waiting for free move command space... Current: " << linesCount << " lines that take " << linesTicksCount / F_CPU_FLOAT << " seconds"  << std::endl);
    pathQueueHasSpace.wait(lk, [this] { return this->doesPathQueueHaveSpace(); });
    linesCacheRemaining = moveCacheSize - linesCount;
    linesTicksRemaining = maxBufferedMoveTime - linesTicksCount;
  }	
  if(stop){
    PyEval_RestoreThread(_save);
    LOG( "Stopped/aborted/Cancelled while waiting for free move command space. linesCount: " << linesCount << std::endl);
    return;
  }

  Path& qp = lines[linesWritePos];

  // Now swap p into the path queue - note that we shouldn't refer to p after this because it won't contain anything useful
  qp = std::move(p);
  
  state = endPos; // update the new state of the machine
  LOG("new state: " << state[0] << " " << state[1] << " " << state[2] << std::endl);

  ////////////////////////////////////////////////////////////////////
  // PERFORM PLANNING
  ////////////////////////////////////////////////////////////////////
  
  updateTrapezoids();
  linesWritePos++;
  linesCacheRemaining--;
  linesTicksRemaining -= qp.getTimeInTicks();

  QUEUELOG("Move queued for the worker" << std::endl);

  if(linesWritePos>=moveCacheSize)
    linesWritePos = 0;

  // Notify the run() thread to work
  if((linesCacheRemaining == 0) || linesTicksRemaining <= 0){
    {
      std::lock_guard<std::mutex> lk(line_mutex);
      linesCount++;
      linesTicksCount += qp.getTimeInTicks();
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
    FLOAT_T jerk = std::fabs(current->getSpeeds()[i] - previous->getSpeeds()[i]);

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
      LOG( "Path planner thread: Need to update parameters! This should not happen!" << std::endl);
      cur->updateStepperPathParameters();
    }

    int moveMask = 0;
    int cancellableMask = 0;
    for(int i=0; i<NUM_AXES; i++){
      moveMask |= (cur->isAxisMove(i) << i);
    }

    if(cur->isCancelable()) {
      for(int i=0; i<NUM_AXES; i++)
	cancellableMask |= (cur->isAxisMove(i) << i);
    }

    LOG("Cancel    mask: " << cancellableMask << std::endl);

    LOG("startSpeed:   " << cur->getStartSpeed() << std::endl);
    LOG("fullSpeed:    " << cur->getFullSpeed() << std::endl);
    LOG("acceleration: " << cur->getAcceleration() << std::endl);

    const FLOAT_T moveEndTime = cur->runFinalStepCalculations();

    LOG("Sending " << std::dec << linesPos << ", Start speed=" << cur->getStartSpeed() << ", end speed=" << cur->getEndSpeed() << std::endl);

    runMove(moveMask, cancellableMask, cur->isSyncEvent(), cur->isSyncWaitEvent(), moveEndTime, cur->getSteps(), commandBlock, maxCommandsPerBlock);

    //LOG("Current move time " << pru.getTotalQueuedMovesTime() / (double) F_CPU << std::endl);

    LOG( "Done sending with " << std::dec << linesPos << std::endl);
		
    removeCurrentLine();
    notifyIfPathQueueHasSpace();
  }
}

inline unsigned long long roundStepTime(FLOAT_T stepTime)
{
  return std::llround(stepTime * (F_CPU_FLOAT / 2000.0)) * 2000;
}

void PathPlanner::runMove(
  const int moveMask,
  const int cancellableMask,
  const bool sync,
  const bool wait,
  const FLOAT_T moveEndTime,
  std::array<std::vector<Step>, NUM_AXES>& steps,
  std::unique_ptr<SteppersCommand[]> const &commands,
  const size_t commandsLength) {

  std::array<unsigned long long, NUM_AXES> finalStepTimes;
  std::array<size_t, NUM_AXES> stepIndex;
  size_t commandsIndex = 0;

  finalStepTimes.fill(0);
  stepIndex.fill(0);

  for (size_t i = 0; i < commandsLength; i++) {
    commands[i] = {};
  }
  
  unsigned long long lastStepTime = 0;

  // sanity check - are there any steps at all?
  {
    bool haveSteps = false;
    for (const auto& axisSteps : steps)
    {
      if (!axisSteps.empty())
      {
        haveSteps = true;
      }
    }

    if (!haveSteps)
    {
      assert(0);
      return;
    }
  }

  // reserve a command to be an opening delay with no steps
  uint32_t* lastDelay = &commands[commandsIndex].delay;
  commandsIndex++;

  // Note that this opening delay doesn't have cancellableMask set - this is intentional because
  // a command that doesn't step anything shouldn't count towards the number of cancelled commands.

  bool foundStep = true;
  while (foundStep)
  {
    SteppersCommand& cmd = commands[commandsIndex];
    commandsIndex++;
    foundStep = false;

    cmd.cancellableMask = cancellableMask;

    // find a step time
    unsigned long long stepTime = UINT64_MAX;

    for (int i = 0; i < NUM_AXES; i++)
    {
      const auto& axisSteps = steps[i];
      const auto axisStepIndex = stepIndex[i];

      if (axisSteps.size() > axisStepIndex)
      {
        stepTime = std::min(stepTime, roundStepTime(axisSteps[axisStepIndex].time));
        foundStep = true;
      }
    }

    if (!foundStep)
    {
      assert(stepTime == UINT64_MAX);
      stepTime = roundStepTime(moveEndTime);
    }

    // set the previous delay
    assert(lastDelay != nullptr);
    assert(stepTime > lastStepTime);
    assert(stepTime - lastStepTime >= 2000);
    assert(stepTime - lastStepTime < F_CPU / 2);

    *lastDelay = stepTime - lastStepTime;

    if (!foundStep)
    {
      QUEUELOG("last step at " << lastStepTime / F_CPU_FLOAT << " and final time at " << roundedStepTime / F_CPU_FLOAT
        << " for a final delay of " << *lastDelay << std::endl);
    }

    lastDelay = &cmd.delay;
    lastStepTime = stepTime;

    // add all the axes that can step at this time
    for (int i = 0; i < NUM_AXES; i++)
    {
      const auto& axisSteps = steps[i];
      const auto axisStepIndex = stepIndex[i];

      if (axisSteps.size() > axisStepIndex && roundStepTime(axisSteps[axisStepIndex].time) == stepTime)
      {
	const auto& step = axisSteps[axisStepIndex];

	assert(!(cmd.step & (1 << i)));
	assert(step.axis == i);

	cmd.step |= 1 << i;
	cmd.direction |= ((unsigned char)step.direction) << i;

	stepIndex[i]++;
	finalStepTimes[i] = stepTime;
      }
    }

    assert(cmd.step != 0 || !foundStep);

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
	LOG("axis " << i << " finished at " << finalStepTimes[i] / F_CPU_FLOAT << std::endl);
	if (finalStepTimes[i] != 0) {
	  earliestFinishTime = std::min(earliestFinishTime, finalStepTimes[i]);
	  latestFinishTime = std::max(latestFinishTime, finalStepTimes[i]);
	}
      }
    }
    LOG("finish times ranged from " << earliestFinishTime << " to " << latestFinishTime << ", which is "
      << latestFinishTime - earliestFinishTime << " ticks or " << (latestFinishTime - earliestFinishTime) / F_CPU_FLOAT << " seconds"
      << std::endl);

    //assert((latestFinishTime - earliestFinishTime) / F_CPU_FLOAT < 10 * CPU_CYCLE_LENGTH); // all axes should finish within 10 PRU cycles
  }

  for (int i = 0; i < NUM_AXES; i++)
  {
    assert(stepIndex[i] == steps[i].size());
  }
}

VectorN PathPlanner::getState()
{
  VectorN output = state.toVectorN() / axisStepsPerM;
  Vector3 motionPos;
  switch (axis_config)
  {
  case AXIS_CONFIG_XY:
    motionPos = output.toVector3();
    break;
  case AXIS_CONFIG_H_BELT:
    motionPos = hBeltToWorld(state.toVectorN().toVector3() / axisStepsPerM.toVector3());
    break;
  case AXIS_CONFIG_CORE_XY:
    motionPos = coreXYToWorld(state.toVectorN().toVector3() / axisStepsPerM.toVector3());
    break;
  case AXIS_CONFIG_DELTA:
    motionPos = delta_bot.deltaToWorld(state.toVectorN().toVector3() / axisStepsPerM.toVector3());
    break;
  default:
    assert(0);
  }

  output[0] = motionPos.x;
  output[1] = motionPos.y;
  output[2] = motionPos.z;

  return output;
}
