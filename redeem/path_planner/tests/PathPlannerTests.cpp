#define _SILENCE_TR1_NAMESPACE_DEPRECATION_WARNING

#include "gmock/gmock.h"
#include "gtest/gtest.h"

#include <condition_variable>
#include <cstring>
#include <mutex>
#include <numeric>
#include <string>
#include <thread>

#include "AlarmCallback.h"
#include "PathPlanner.h"
#include "PruInterface.h"
#include "TestUtils.h"
#include "vector3.h"
#include "vectorN.h"

class MockAlarmCallback : public AlarmCallback
{
public:
    MOCK_METHOD3(call, void(int type, std::string message, std::string shortMessage));
};

class MockPru : public PruInterface
{
public:
    std::mutex mutex;
    std::condition_variable onBlockPushed;
    std::vector<SteppersCommand> stepperCommands;
    std::vector<uint64_t> blockTimes;
    std::vector<SyncCallback*> callbacks;

    uint64_t totalTime = 0;
    uint32_t numberOfBlocksPushed = 0;

    MOCK_METHOD2(initPRU, bool(const std::string&, const std::string&));
    MOCK_METHOD0(run, void());

    MOCK_METHOD0(getFreeMemory, size_t());
    MOCK_METHOD0(getTotalQueuedMovesTime, uint64_t());
    MOCK_METHOD0(suspend, void());
    MOCK_METHOD0(resume, void());
    MOCK_METHOD0(reset, void());
    MOCK_METHOD0(getStepsRemaining, size_t());

    void pushBlock(uint8_t* start, size_t length, unsigned int unit, uint64_t time, SyncCallback* callback) override
    {
        std::unique_lock<std::mutex> lock(mutex);

        ASSERT_EQ(unit, sizeof(SteppersCommand));
        ASSERT_EQ(length % sizeof(SteppersCommand), 0);

        auto commandStart = reinterpret_cast<SteppersCommand*>(start);

        stepperCommands.insert(stepperCommands.end(), commandStart, commandStart + (length / sizeof(SteppersCommand)));
        blockTimes.push_back(time);

        if (callback != nullptr)
        {
            callbacks.push_back(callback);
        }

        totalTime += time;

        std::memset(start, 0, length);
        numberOfBlocksPushed++;

        onBlockPushed.notify_all();
    }

    void runThread() override
    {
    }

    void waitUntilFinished() override
    {
    }

    void stopThread(bool) override
    {
    }

    size_t getMaxBytesPerBlock() override
    {
        return 128;
    }

    void waitForBlock()
    {
        std::unique_lock<std::mutex> lock(mutex);
        const auto startBlocksPushed = numberOfBlocksPushed;
        onBlockPushed.wait(lock, [this, startBlocksPushed]() { return numberOfBlocksPushed != startBlocksPushed; });
    }
};

class PathPlannerRunMoveTest : public ::testing::Test
{
protected:
    MockAlarmCallback alarmCallback;
    MockPru pru;
    PathPlanner planner;

public:
    PathPlannerRunMoveTest()
        : alarmCallback()
        , pru()
        , planner(1024, alarmCallback, pru)
    {
    }

    void runMove(
        const int moveMask,
        const int cancellableMask,
        const bool sync,
        const bool wait,
        const double moveEndTime,
        std::array<std::vector<Step>, NUM_AXES>& steps,
        std::unique_ptr<SteppersCommand[]> const& commands,
        const size_t commandsLength,
        IntVectorN* probeDistanceTraveled)
    {
        planner.runMove(moveMask, cancellableMask, sync, wait, moveEndTime, steps, commands, commandsLength, probeDistanceTraveled);
    }
};

bool operator==(const SteppersCommand& l, const SteppersCommand& r)
{
    auto leftPointer = reinterpret_cast<const uint8_t*>(&l);
    auto rightPointer = reinterpret_cast<const uint8_t*>(&r);
    for (size_t byteIndex = 0; byteIndex < sizeof(SteppersCommand); byteIndex++)
    {
        if (leftPointer[byteIndex] != rightPointer[byteIndex])
        {
            return false;
        }
    }
    return true;
}

bool operator!=(const SteppersCommand& l, const SteppersCommand& r)
{
    return !operator==(l, r);
}

std::ostream& operator<<(std::ostream& stream, const SteppersCommand& command)
{
    return stream << "step: " << (int)command.step << " direction: " << (int)command.direction << " cancellableMask: " << (int)command.cancellableMask << " options: " << (int)command.options << " delay: " << (int)command.delay;
}

TEST_F(PathPlannerRunMoveTest, WritesWithinBufferLength)
{
    std::array<std::vector<Step>, NUM_AXES> steps;

    steps[X_AXIS].push_back(Step(0.1, X_AXIS, true));
    steps[X_AXIS].push_back(Step(0.2, X_AXIS, true));

    const size_t commandLength = 2;
    std::unique_ptr<SteppersCommand[]> commands = std::make_unique<SteppersCommand[]>(commandLength + 1);

    std::memset(&commands[commandLength], 0xffffffff, sizeof(SteppersCommand));

    runMove(1, 0, false, false, 0.3, steps, commands, commandLength, nullptr);

    EXPECT_EQ(commands[commandLength].step, 0xff);
}

TEST_F(PathPlannerRunMoveTest, PushesCorrectNumberOfBlocks)
{
    std::array<std::vector<Step>, NUM_AXES> steps;

    steps[X_AXIS].push_back(Step(0.1, X_AXIS, true));
    steps[X_AXIS].push_back(Step(0.2, X_AXIS, true));

    const size_t commandLength = 2;
    std::unique_ptr<SteppersCommand[]> commands = std::make_unique<SteppersCommand[]>(commandLength);

    runMove(1, 0, false, false, 0.3, steps, commands, commandLength, nullptr);

    EXPECT_EQ(pru.stepperCommands.size(), 3); // one for opening wait, then two steps
}

TEST_F(PathPlannerRunMoveTest, CalculatesWaitsCorrectly)
{
    std::array<std::vector<Step>, NUM_AXES> steps;

    steps[X_AXIS].push_back(Step(0.01, X_AXIS, true));
    steps[X_AXIS].push_back(Step(0.03, X_AXIS, true));
    steps[X_AXIS].push_back(Step(0.06, X_AXIS, true));
    steps[X_AXIS].push_back(Step(0.10, X_AXIS, true));
    steps[X_AXIS].push_back(Step(0.15, X_AXIS, true));

    const size_t commandLength = 2;
    std::unique_ptr<SteppersCommand[]> commands = std::make_unique<SteppersCommand[]>(commandLength);

    runMove(1, 0, false, false, 0.21, steps, commands, commandLength, nullptr);

    auto& stepsTaken = pru.stepperCommands;
    ASSERT_EQ(stepsTaken.size(), 6);
    EXPECT_EQ(stepsTaken[0].delay, 0.01 * F_CPU);
    EXPECT_EQ(stepsTaken[1].delay, 0.02 * F_CPU);
    EXPECT_EQ(stepsTaken[2].delay, 0.03 * F_CPU);
    EXPECT_EQ(stepsTaken[3].delay, 0.04 * F_CPU);
    EXPECT_EQ(stepsTaken[4].delay, 0.05 * F_CPU);
    EXPECT_EQ(stepsTaken[5].delay, 0.06 * F_CPU);
}

TEST_F(PathPlannerRunMoveTest, WrapsStepListsCorrectly)
{
    std::array<std::vector<Step>, NUM_AXES> steps;

    steps[X_AXIS].reserve(100);

    for (int stepIndex = 0; stepIndex < 100; stepIndex++)
    {
        const double stepTime = 0.01 * stepIndex + 0.005;
        Step step(stepTime, X_AXIS, true);
        steps[X_AXIS].push_back(step);
    }

    EXPECT_DOUBLE_EQ(steps[X_AXIS][0].time, 0.005);
    EXPECT_DOUBLE_EQ(steps[X_AXIS][99].time, 0.995);

    EXPECT_EQ(steps[X_AXIS].size(), 100);

    const size_t commandLength = 10;
    std::unique_ptr<SteppersCommand[]> commands = std::make_unique<SteppersCommand[]>(commandLength);

    runMove(0x1, 0, false, false, 1.0, steps, commands, commandLength, nullptr);

    // we're moving at one step every 0.01 seconds, which is 2,000,000 PRU cycles
    const SteppersCommand openingWait = { 0, 0, 0, 0, 1000000 };
    const SteppersCommand normalStep = { 1, 1, 0, 0, 2000000 };
    const SteppersCommand endStep = { 1, 1, 0, 0, 1000000 };

    auto& stepCommands = pru.stepperCommands;

    EXPECT_EQ(stepCommands.size(), 101); // one extra for the opening wait
    EXPECT_EQ(stepCommands[0], openingWait);
    EXPECT_EQ(stepCommands[stepCommands.size() - 1], endStep);

    for (int step = 1; step < 100; step++)
    {
        if (stepCommands[step] != normalStep)
        {
            EXPECT_EQ(step, -1);
            EXPECT_EQ(stepCommands[step], normalStep);
        }
    }
}

TEST_F(PathPlannerRunMoveTest, SpecifiesCorrectBlockTimes)
{
    std::array<std::vector<Step>, NUM_AXES> steps;

    steps[X_AXIS].push_back(Step(0.01, X_AXIS, true));
    steps[X_AXIS].push_back(Step(0.03, X_AXIS, true));
    steps[X_AXIS].push_back(Step(0.06, X_AXIS, true));
    steps[X_AXIS].push_back(Step(0.10, X_AXIS, true));
    steps[X_AXIS].push_back(Step(0.15, X_AXIS, true));

    const size_t commandLength = 2;
    std::unique_ptr<SteppersCommand[]> commands = std::make_unique<SteppersCommand[]>(commandLength);

    runMove(1, 0, false, false, 0.21, steps, commands, commandLength, nullptr);

    auto& blockTimes = pru.blockTimes;
    ASSERT_EQ(blockTimes.size(), 3);
    EXPECT_DOUBLE_EQ(static_cast<double>(blockTimes[0]), (0.01 + 0.02) * F_CPU);
    EXPECT_DOUBLE_EQ(static_cast<double>(blockTimes[1]), (0.03 + 0.04) * F_CPU);
    EXPECT_DOUBLE_EQ(static_cast<double>(blockTimes[2]), (0.05 + 0.06) * F_CPU);
}

class PathPlannerTest : public ::testing::Test
{
protected:
    MockAlarmCallback alarmCallback;
    MockPru pru;
    PathPlanner planner;

public:
    PathPlannerTest()
        : alarmCallback()
        , pru()
        , planner(1024, alarmCallback, pru)
    {
        planner.setState(VectorN());
        planner.setMaxSpeeds(VectorN(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0));
        planner.setAxisStepsPerMeter(VectorN(100000, 100000, 100000, 100000, 100000, 100000, 100000, 100000));
        planner.setAcceleration(VectorN(1, 1, 1, 1, 1, 1, 1, 1));
        planner.setMaxSpeedJumps(VectorN(0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01));
    }

    uint64_t getQueuedMoveTime()
    {
        return planner.pathQueue.getQueuedMoveTime();
    }
};

TEST_F(PathPlannerTest, RunsSimplePath)
{
    planner.queueMove(
        VectorN(0.001, 0, 0), // at 100 steps/mm, this will take 100 steps to complete
        0.001, // at 1mm/s, this should take 1 second
        1.0,
        false,
        false, // TODO what does this even do?
        false,
        false,
        false,
        false);

    planner.runThread();
    planner.waitUntilFinished();
    planner.stopThread(true);

    auto& commands = pru.stepperCommands;

    // for 100 steps in 1 second, each step should take 0.01 seconds (which is 2000000 PRU cycles)

    ASSERT_EQ(commands.size(), 101); // one extra for the initial wait
    SteppersCommand firstCommand = {
        0,
        0,
        0,
        0,
        static_cast<uint32_t>(std::lround(0.01 * F_CPU / 2))
    };

    SteppersCommand normalCommand = {
        1, // step X
        1, // in the positive direction
        0, // not cancellable
        0, // no options
        static_cast<uint32_t>(std::lround(0.01 * F_CPU))
    };

    SteppersCommand lastCommand = {
        1,
        1,
        0,
        0,
        static_cast<uint32_t>(std::lround(0.01 * F_CPU / 2))
    };

    EXPECT_EQ(commands[0], firstCommand);
    EXPECT_EQ(commands[100], lastCommand);

    for (int i = 1; i < 100; i++)
    {
        EXPECT_EQ(commands[i], normalCommand);
    }
}

TEST_F(PathPlannerTest, TracksBufferedMoveTime)
{
    planner.queueMove(
        VectorN(0.001, 0, 0), // at 100 steps/mm, this will take 100 steps to complete
        0.001, // at 1mm/s, this should take 1 second
        1.0,
        false,
        false, // TODO what does this even do?
        false,
        false,
        false,
        false);

    EXPECT_EQ(getQueuedMoveTime(), 1.0 * F_CPU);

    planner.runThread();
    planner.waitUntilFinished();
    planner.stopThread(true);

    EXPECT_EQ(getQueuedMoveTime(), 0);
}

struct TestSyncCallback : public SyncCallback
{
    std::promise<void> syncPromise;
    std::future<void> syncFuture;

    TestSyncCallback()
        : syncPromise()
        , syncFuture(syncPromise.get_future())
    {
    }

    void syncComplete() override
    {
        syncPromise.set_value();
    }
};

TEST_F(PathPlannerTest, PassesSyncCallbacksToPru)
{
    TestSyncCallback callback;

    planner.queueSyncEvent(callback);

    planner.runThread();
    planner.waitUntilFinished();
    planner.stopThread(true);

    ASSERT_EQ(pru.callbacks.size(), 1);
    ASSERT_EQ(pru.callbacks[0], &callback);

    ASSERT_FALSE(is_ready(callback.syncFuture));

    pru.callbacks[0]->syncComplete();

    ASSERT_TRUE(is_ready(callback.syncFuture));

    EXPECT_EQ(pru.stepperCommands.size(), 1);
    SteppersCommand expectedCommand = { 0, 0, 0, STEPPER_COMMAND_OPTION_SYNC_EVENT, 0 };
    // long-term TODO - the new use of callbacks that can trigger when an arbitrary command block completes
    // makes the older sync event system irrelevant. It should be removed.
    EXPECT_EQ(pru.stepperCommands[0], expectedCommand);
}

TEST_F(PathPlannerTest, WaitsForWaitEvents)
{
    auto blockReadyFuture = std::async(std::launch::async, [this]() { pru.waitForBlock(); });

    planner.runThread();

    planner.queueMove(
        VectorN(0.0001, 0, 0), // at 100 steps/mm, this will take 10 steps to complete
        0.0001, // at 0.1mm/s, this should take 1 second
        1.0,
        false,
        false, // TODO what does this even do?
        false,
        false,
        false,
        false);

    auto waitEvent = planner.queueWaitEvent();

    planner.queueMove(
        VectorN(0.0002, 0, 0), // at 100 steps/mm, this will take 10 steps to complete
        0.0001, // at 0.1mm/s, this should take 1 second
        1.0,
        false,
        false, // TODO what does this even do?
        false,
        false,
        false,
        false);

    blockReadyFuture.wait();

    // this test is by nature a race condition - if the path planner doesn't wait properly, it will continue to process the second path
    std::this_thread::sleep_for(std::chrono::milliseconds(1));

    ASSERT_EQ(pru.stepperCommands.size(), 11);

    waitEvent->signalWaitComplete();
    planner.waitUntilFinished();
    planner.stopThread(true);

    ASSERT_EQ(pru.stepperCommands.size(), 23); // one extra for the wait event - TODO this can be improved
}