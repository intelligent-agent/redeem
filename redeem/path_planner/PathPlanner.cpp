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
#include <algorithm>
#include <array>
#include <assert.h>
#include <cmath>
#include <thread>

PathPlanner::PathPlanner(unsigned int cacheSize, AlarmCallback& alarmCallback, PruInterface& pru)
    : alarmCallback(alarmCallback)
    , pru(pru)
    , optimizer()
    , pathQueue(optimizer, cacheSize, 10 * F_CPU) // TODO pass time
{
    // Force out a log message even if the log level would suppress it
    Logger() << "INFO     "
             << "PathPlanner loglevel is " << LOGLEVEL << std::endl;
    stop = false;
    acceptingPaths = true;

    axis_config = AXIS_CONFIG_XY;
    has_slaves = false;
    master.clear();
    slave.clear();

    for (int axis = 0; axis < NUM_AXES; axis++)
    {
        axes_stepping_together[axis] = 1 << axis;
    }

    state.zero();
    lastProbeDistance = 0;
    queue_move_fail = true;

    // set bed compensation matrix to identity
    matrix_bed_comp.resize(9, 0);
    matrix_bed_comp[0] = 1.0;
    matrix_bed_comp[4] = 1.0;
    matrix_bed_comp[8] = 1.0;

    recomputeParameters();

    LOGINFO("PathPlanner initialized\n");
}

#ifndef USE_FAKE_PRU_INTERFACE
PathPlanner::PathPlanner(unsigned int cacheSize, AlarmCallback& alarmCallback)
    : PathPlanner(cacheSize, alarmCallback, *new PruTimer([this]() { this->pruAlarmCallback(); }))
{
}
#endif

void PathPlanner::recomputeParameters()
{
    for (int i = 0; i < NUM_AXES; i++)
    {
        /** Acceleration in steps/s^2 in printing mode.*/
        maxAccelerationStepsPerSquareSecond[i] = maxAccelerationMPerSquareSecond[i] * axisStepsPerM[i];
    }
}

void PathPlanner::queueSyncEvent(SyncCallback& callback, bool isBlocking)
{
    pathQueue.queueSyncEvent(callback, isBlocking);
}

WaitEvent* PathPlanner::queueWaitEvent()
{
    WaitEvent* waitEvent = new WaitEvent();

    pathQueue.queueWaitEvent(waitEvent->getFuture());

    return waitEvent;
}

void PathPlanner::queueMove(VectorN endWorldPos,
    double speed, double accel,
    bool cancelable, bool optimize,
    bool enable_soft_endstops, bool use_bed_matrix,
    bool use_backlash_compensation, bool is_probe,
    int tool_axis)
{
    ////////////////////////////////////////////////////////////////////
    // PRE-PROCESSING
    ////////////////////////////////////////////////////////////////////

    queue_move_fail = true;

    if (!acceptingPaths)
    {
        LOGWARNING("Rejecting path because path planner is suspended" << std::endl);
        return;
    }

    LOG("NEW MOVE:\n");
    // for (int i = 0; i<NUM_AXES; ++i) {
    //   LOG("AXIS " << i << ": start = " << startPos[i] << "(" << state[i] << "), end = " << endPos[i] << "\n");
    // }

    VectorN startWorldPos = getState();

    // Cap the end position based on soft end stops
    if (enable_soft_endstops)
    {
        int endstop = softEndStopApply(endWorldPos);
        if (endstop)
        {
            LOGERROR("soft endstop triggered - suspending path planner and triggering alarm" << std::endl);
            acceptingPaths = false;
            switch (endstop)
            {
            case 1:
                alarmCallback.call(8, "Soft endstop hit", "Soft endstop hit: X min");
                break;
            case 2:
                alarmCallback.call(8, "Soft endstop hit", "Soft endstop hit: Y min");
                break;
            case 3:
                alarmCallback.call(8, "Soft endstop hit", "Soft endstop hit: Z min");
                break;
            case 11:
                alarmCallback.call(8, "Soft endstop hit", "Soft endstop hit: X max");
                break;
            case 12:
                alarmCallback.call(8, "Soft endstop hit", "Soft endstop hit: Y max");
                break;
            case 13:
                alarmCallback.call(8, "Soft endstop hit", "Soft endstop hit: Z max");
                break;
            default:
                alarmCallback.call(8, "Soft endstop hit", "Soft endstop hit: unknown");
            }
            return;
        }
    }
    // Calculate the position to reach, with bed levelling
    if (use_bed_matrix)
    {
        LOG("Before matrix X: " << endWorldPos[0] << " Y: " << endWorldPos[1] << " Z: " << endWorldPos[2] << "\n");
        applyBedCompensation(endWorldPos);
        LOG("After matrix X: " << endWorldPos[0] << " Y: " << endWorldPos[1] << " Z: " << endWorldPos[2] << "\n");
    }

    // clear any movements on slave axes so they don't mess things up later
    clearSlaveAxesMovements(startWorldPos, endWorldPos);

    // Get the vector to move us from where we are, to where we ideally want to be.
    bool possibleMove = true;
    IntVectorN endPos = worldToMachine(endWorldPos, &possibleMove);

    if (!possibleMove)
    {
        LOGERROR("attempted move to impossible position - suspending path planner and triggering alarm" << std::endl);
        acceptingPaths = false;
        alarmCallback.call(9, "Move to unreachable position requested", "Move to unreachable position requested");
        return;
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

    for (int i = 0; i < NUM_AXES; i++)
    {
        if (rawDeltas[i] != 0)
        {
            move = true;
            break;
        }
    }

    // check for a no-move
    if (!move)
    {
        LOGINFO("no move" << std::endl);
        return;
    }

    IntVectorN tweakedEndPos = endPos;

    // backlash compensation
    if (use_backlash_compensation)
    {
        IntVectorN adjustedDeltas = rawDeltas;
        backlashCompensation(adjustedDeltas);

        tweakedEndPos = state + adjustedDeltas;
    }

    ////////////////////////////////////////////////////////////////////
    // LOAD INTO QUEUE
    ////////////////////////////////////////////////////////////////////

    Path p;

    p.initialize(state, tweakedEndPos, startWorldPos, endWorldPos, axisStepsPerM,
        maxSpeeds, maxAccelerationMPerSquareSecond,
        speed, accel, axis_config, delta_bot, cancelable, is_probe);

    if (p.isNoMove())
    {
        LOGINFO("Warning: no move path" << std::endl);
        assert(0); /// TODO We should have bailed before now
        return; // No steps included
    }

    std::optional<std::future<IntVectorN>> probeResult;

    if (is_probe)
    {
        probeResult = p.prepareProbeResult();
    }

    /*
    LOG("checking deltas..." << std::endl);
    std::cout.flush();
    {
        IntVectorN realDeltas;

        for (const auto& axisSteps : p.getSteps())
        {
            double lastTime = 0;
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
	*/

    if (!pathQueue.addPath(std::move(p)))
    {
        return;
    }

    // capture state so we can check it after a probe
    const IntVectorN startPos = state;

    if (!is_probe)
    {
        state = endPos; // update the new state of the machine
        LOG("new state: " << state[0] << " " << state[1] << " " << state[2] << std::endl);
    }
    else
    {
        LOG("probe move - getting new state once probe completes" << std::endl);
        assert((bool)probeResult);
        auto& value = probeResult.value();
        value.wait();
        state = value.get();

        assert(state != startPos);
    }

    ////////////////////////////////////////////////////////////////////
    // PERFORM PLANNING
    ////////////////////////////////////////////////////////////////////

    //    LOGINFO("Move queued for the worker" << std::endl);

    queue_move_fail = false;
}

void PathPlanner::runThread()
{
    stop = false;
    LOGINFO("PathPlanner: starting thread" << std::endl);
    pru.runThread();
    runningThread = std::thread([this]() {
        this->run();
    });
}

void PathPlanner::stopThread(bool join)
{
    pru.stopThread(join);
    stop = true;

    pathQueue.stop();

    if (join && runningThread.joinable())
    {
        runningThread.join();
    }
}

PathPlanner::~PathPlanner()
{
    if (runningThread.joinable())
    {
        stopThread(true);
    }
}

void PathPlanner::waitUntilFinished()
{
    pathQueue.waitForQueueToEmpty();

    //Wait for PruTimer then
    if (!stop)
    {
        pru.waitUntilFinished();
    }
}

void PathPlanner::reset()
{
    LOGINFO("path planner resetting" << std::endl);
    pru.reset();
    acceptingPaths = true;
}

void PathPlanner::run()
{
    LOGINFO("PathPlanner loop starting" << std::endl);

    const unsigned int maxCommandsPerBlock = pru.getMaxBytesPerBlock() / sizeof(SteppersCommand);
    std::unique_ptr<SteppersCommand[]> commandBlock(new SteppersCommand[maxCommandsPerBlock]);

    while (!stop)
    {
        auto possiblePath = pathQueue.popPath();

        if (!possiblePath)
        {
            // the queue should only fail to give us a path if we're shutting down
            assert(stop);
            continue;
        }
        Path& cur = possiblePath.value();

        // TODO check for wait events and wait (with tests)

        IntVectorN probeDistanceTraveled;

        assert(!cur.isBlocked());

        // Only enable axes that are moving. If the axis doesn't need to move then it can stay disabled depending on configuration.
        cur.fixStartAndEndSpeed();
        if (!cur.areParameterUpToDate())
        { // should never happen, but with bad timings???
            cur.updateStepperPathParameters();
        }

        LOG("axis mask:    " << cur.getAxisMoveMask() << std::endl);
        LOG("startSpeed:   " << cur.getStartSpeed() << std::endl);
        LOG("fullSpeed:    " << cur.getFullSpeed() << std::endl);
        LOG("acceleration: " << cur.getAcceleration() << std::endl);
        LOG("cancellable:  " << cur.isCancelable() << std::endl);

        const double moveEndTime = cur.runFinalStepCalculations();

        if (cur.isWaitEvent())
        {
            LOGINFO("wait event - path planner thread waiting" << std::endl);
            cur.getWaitEvent().wait();
            LOGINFO("wait event done - path planner thread continuing" << std::endl);
        }

        LOG("Sending, Start speed=" << cur.getStartSpeed() << ", end speed=" << cur.getEndSpeed() << std::endl);

        runMove(cur.getAxisMoveMask(),
            cur.isCancelable() ? cur.getAxisMoveMask() : 0,
            cur.isSyncEvent(),
            cur.isSyncWaitEvent(),
            moveEndTime,
            cur.getSteps(),
            commandBlock,
            maxCommandsPerBlock,
            cur.isProbeMove() ? &probeDistanceTraveled : nullptr,
            cur.getSyncCallback());

        if (cur.isProbeMove())
        {
            const VectorN startPos = machineToWorld(cur.getStartMachinePos());

            assert(state == cur.getStartMachinePos());
            const IntVectorN endMachinePos = cur.getStartMachinePos() + probeDistanceTraveled;
            const VectorN endPos = machineToWorld(endMachinePos);

            lastProbeDistance = vabs(endPos - startPos);

            cur.setProbeResult(endMachinePos);
        }

        //LOG("Current move time " << pru.getTotalQueuedMovesTime() / (double) F_CPU << std::endl);

        LOG("Done sending" << std::endl);
    }
}

inline uint64_t roundStepTime(double stepTime)
{
    return static_cast<uint64_t>(std::llround(stepTime * (F_CPU_FLOAT / MINIMUM_STEP_INTERVAL))) * MINIMUM_STEP_INTERVAL;
}

void PathPlanner::runMove(
    const int moveMask,
    const int cancellableMask,
    const bool sync,
    const bool wait,
    const double moveEndTime,
    std::array<std::vector<Step>, NUM_AXES>& steps,
    std::unique_ptr<SteppersCommand[]> const& commands,
    const size_t commandsLength,
    IntVectorN* probeDistanceTraveled,
    SyncCallback* callback)
{

    std::array<unsigned long long, NUM_AXES> finalStepTimes;
    std::array<size_t, NUM_AXES> stepIndex;
    size_t commandsIndex = 0;
    std::vector<SteppersCommand> probeSteps;
    unsigned int totalSteps = 0;
    uint64_t currentBlockStartTime = 0;

    assert(commandsLength > 1); // we do not handle single-index command buffers correctly

    finalStepTimes.fill(0);
    stepIndex.fill(0);

    for (size_t i = 0; i < commandsLength; i++)
    {
        commands[i] = {};
    }

    unsigned long long lastStepTime = 0;

    // reserve a command to be an opening delay with no steps
    uint32_t* lastDelay = &commands[commandsIndex].delay;
    commandsIndex++;
    totalSteps++;

    // Note that this opening delay doesn't have cancellableMask set - this is intentional because
    // a command that doesn't step anything shouldn't count towards the number of cancelled commands.

    bool foundStep = true;
    uint64_t stepTime = 0;
    while (foundStep)
    {
        foundStep = false;

        // find a step time
        stepTime = UINT64_MAX;

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
            LOG("last step - previousStepTime was " << lastStepTime << " and the move should end at " << stepTime << std::endl);
        }

        // set the previous delay
        assert(lastDelay != nullptr);
        assert(stepTime > lastStepTime || (!foundStep && stepTime == lastStepTime));
        assert(stepTime - lastStepTime >= MINIMUM_STEP_INTERVAL || !foundStep);
        assert(stepTime - lastStepTime < F_CPU / 2);

        *lastDelay = (uint32_t)(stepTime - lastStepTime);

        // find a command to hold the step we're about to take
        if (commandsIndex == commandsLength)
        {
            pru.pushBlock((uint8_t*)&commands[0], sizeof(SteppersCommand) * commandsIndex, sizeof(SteppersCommand), stepTime - currentBlockStartTime);

            if (probeDistanceTraveled)
            {
                probeSteps.insert(probeSteps.end(), &commands[0], &commands[commandsLength]);
            }

            commandsIndex = 0;
            currentBlockStartTime = stepTime;

            for (size_t i = 0; i < commandsLength; i++)
            {
                commands[i] = {};
            }
        }

        if (!foundStep)
        {
            break;
        }

        SteppersCommand& cmd = commands[commandsIndex];
        commandsIndex++;
        totalSteps++;

        cmd.cancellableMask = cancellableMask;

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

                assert(!(cmd.step & (1 << i))); // this means we're double-stepping an axis
                assert(step.axis == i);

                cmd.step |= axes_stepping_together[i];
                cmd.direction |= (step.direction ? 0xff : 0) & axes_stepping_together[i];

                stepIndex[i]++;
                finalStepTimes[i] = stepTime;
            }
        }

        assert(cmd.step != 0);
    }

    if (sync || callback != nullptr)
    {
        // if we have a callback, we need to make sure there's at least one more command to push
        if (commandsIndex == 0)
        {
            commandsIndex = 1;
            totalSteps++;
            LOG("needed a dummy step for synchronization" << std::endl);
            assert(commandsIndex < commandsLength);
            assert(commands[commandsIndex].step == 0 && commands[commandsIndex].delay == 0);
        }

        assert(commandsIndex > 0 && commandsIndex <= commandsLength);

        SteppersCommand& cmd = commands[commandsIndex - 1];
        if (wait)
        {
            cmd.options = STEPPER_COMMAND_OPTION_SYNCWAIT_EVENT;
        }

        if (sync)
        {
            cmd.options = STEPPER_COMMAND_OPTION_SYNC_EVENT;
        }
    }

    if (commandsIndex != 0)
    {
        pru.pushBlock((uint8_t*)&commands[0], sizeof(SteppersCommand) * commandsIndex, sizeof(SteppersCommand), stepTime - currentBlockStartTime, callback);

        if (probeDistanceTraveled)
        {
            probeSteps.insert(probeSteps.end(), &commands[0], &commands[commandsIndex]);
        }

        for (size_t i = 0; i < commandsLength; i++)
        {
            commands[i] = {};
        }
    }

    LOG("move needed " << totalSteps << " steps" << std::endl);

    for (int i = 0; i < NUM_AXES; i++)
    {
        assert(stepIndex[i] == steps[i].size());
    }

    if (probeDistanceTraveled)
    {
        pru.waitUntilFinished();
        const size_t stepsRemaining = pru.getStepsRemaining();
        const size_t stepsTraveled = probeSteps.size() - stepsRemaining;

        assert(stepsRemaining < probeSteps.size());
        IntVectorN deltasTraveled;

        for (size_t i = 0; i < stepsTraveled; i++)
        {
            for (int axis = 0; axis < NUM_AXES; axis++)
            {
                const SteppersCommand& command = probeSteps[i];
                if (command.step & (1 << axis))
                {
                    deltasTraveled[axis] += (command.direction & (1 << axis)) ? 1 : -1;
                }
            }
        }

        // Zero out any slave axes - it's easier to do so here than in the loop
        if (has_slaves)
        {
            for (auto slaveAxis : slave)
            {
                deltasTraveled[slaveAxis] = 0;
            }
        }

        *probeDistanceTraveled = deltasTraveled;
    }
}

VectorN PathPlanner::machineToWorld(const IntVectorN& machinePos)
{
    VectorN output = machinePos.toVectorN() / axisStepsPerM;
    Vector3 motionPos;
    switch (axis_config)
    {
    case AXIS_CONFIG_XY:
        motionPos = output.toVector3();
        break;
    case AXIS_CONFIG_H_BELT:
        motionPos = hBeltToWorld(machinePos.toVectorN().toVector3() / axisStepsPerM.toVector3());
        break;
    case AXIS_CONFIG_CORE_XY:
        motionPos = coreXYToWorld(machinePos.toVectorN().toVector3() / axisStepsPerM.toVector3());
        break;
    case AXIS_CONFIG_DELTA:
        motionPos = delta_bot.deltaToWorld(machinePos.toVectorN().toVector3() / axisStepsPerM.toVector3());
        break;
    default:
        assert(0);
    }

    output[0] = motionPos.x;
    output[1] = motionPos.y;
    output[2] = motionPos.z;

    return output;
}

VectorN PathPlanner::getState()
{
    return machineToWorld(state);
}

bool PathPlanner::getLastQueueMoveStatus()
{
    return queue_move_fail;
}

IntVectorN PathPlanner::worldToMachine(const VectorN& worldPos, bool* possible)
{
    IntVectorN output = (worldPos * axisStepsPerM).round();

    if (possible)
    {
        *possible = true;
    }

    switch (axis_config)
    {
    case AXIS_CONFIG_DELTA:
    {
        const Vector3 deltaEnd = delta_bot.worldToDelta(worldPos.toVector3());
        LOG("Delta end: X: " << deltaEnd[0] << " Y: " << deltaEnd[1] << " Z: " << deltaEnd[2] << std::endl);
        const IntVector3 endMotionPos = (deltaEnd * axisStepsPerM.toVector3()).round();
        LOG("Delta end motors: X: " << endMotionPos[0] << " Y: " << endMotionPos[1] << " Z: " << endMotionPos[2] << std::endl);
        output[0] = endMotionPos[0];
        output[1] = endMotionPos[1];
        output[2] = endMotionPos[2];

        if (possible)
        {
            // If any of the tower positions are NaN, the move is impossible
            *possible = !deltaEnd.hasNan();
        }
        break;
    }
    case AXIS_CONFIG_CORE_XY:
    {
        const Vector3 coreXYEnd = worldToCoreXY(worldPos.toVector3());
        const IntVector3 endMotionPos = (coreXYEnd * axisStepsPerM.toVector3()).round();

        output[0] = endMotionPos[0];
        output[1] = endMotionPos[1];
        assert(output[2] == endMotionPos[2]);
        output[2] = endMotionPos[2];
        break;
    }
    case AXIS_CONFIG_H_BELT:
    {
        const Vector3 hBeltEnd = worldToHBelt(worldPos.toVector3());
        const IntVector3 endMotionPos = (hBeltEnd * axisStepsPerM.toVector3()).round();

        output[0] = endMotionPos[0];
        output[1] = endMotionPos[1];
        assert(output[2] == endMotionPos[2]);
        output[2] = endMotionPos[2];
        break;
    }
    case AXIS_CONFIG_XY:
        break;
    default:
        output.zero();
        LOG("don't know what to do for axis config: " << axis_config << std::endl);
        assert(0);
        break;
    }

    return output;
}
void AlarmCallback::call(int alarmType, std::string message, std::string shortMessage)
{
    assert(0); // this method will be overridden by child classes - SWIG takes care of it
}

AlarmCallback::~AlarmCallback()
{
}
