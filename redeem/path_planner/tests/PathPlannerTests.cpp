#define _SILENCE_TR1_NAMESPACE_DEPRECATION_WARNING

#include "gmock/gmock.h"
#include "gtest/gtest.h"

#include <numeric>
#include <string>

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
    std::vector<SteppersCommand> pushedBlocks;
    std::vector<uint64_t> blockTimes;
    uint64_t totalTime = 0;
    uint32_t blocksPushed = 0;

    MOCK_METHOD2(initPRU, bool(const std::string&, const std::string&));
    MOCK_METHOD0(run, void());
    MOCK_METHOD0(runThread, void());
    MOCK_METHOD1(stopThread, void(bool));
    MOCK_METHOD0(waitUntilFinished, void());
    MOCK_METHOD0(getFreeMemory, size_t());
    MOCK_METHOD0(getTotalQueuedMovesTime, uint64_t());
    MOCK_METHOD0(getMaxBytesPerBlock, size_t());
    MOCK_METHOD0(waitUntilSync, int());
    MOCK_METHOD0(suspend, void());
    MOCK_METHOD0(resume, void());
    MOCK_METHOD0(reset, void());

    void push_block(uint8_t* start, size_t length, unsigned int unit, uint64_t time)
    {
        ASSERT_EQ(unit, sizeof(SteppersCommand));
        ASSERT_EQ(length % sizeof(SteppersCommand), 0);

        auto commandStart = reinterpret_cast<SteppersCommand*>(start);

        pushedBlocks.insert(pushedBlocks.end(), commandStart, commandStart + (length / sizeof(SteppersCommand)));
        blockTimes.push_back(time);
        totalTime += time;

        std::memset(start, 0, length);
        blocksPushed++;
    }

    MOCK_METHOD0(getStepsRemaining, size_t());
};

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

TEST_F(PathPlannerTest, WritesWithinBufferLength)
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

TEST_F(PathPlannerTest, PushesCorrectNumberOfBlocks)
{
    std::array<std::vector<Step>, NUM_AXES> steps;

    steps[X_AXIS].push_back(Step(0.1, X_AXIS, true));
    steps[X_AXIS].push_back(Step(0.2, X_AXIS, true));

    const size_t commandLength = 2;
    std::unique_ptr<SteppersCommand[]> commands = std::make_unique<SteppersCommand[]>(commandLength);

    runMove(1, 0, false, false, 0.3, steps, commands, commandLength, nullptr);

    EXPECT_EQ(pru.pushedBlocks.size(), 3); // one for opening wait, then two steps
}

TEST_F(PathPlannerTest, CalculatesWaitsCorrectly)
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

    auto& stepsTaken = pru.pushedBlocks;
    ASSERT_EQ(stepsTaken.size(), 6);
    EXPECT_EQ(stepsTaken[0].delay, 0.01 * F_CPU);
    EXPECT_EQ(stepsTaken[1].delay, 0.02 * F_CPU);
    EXPECT_EQ(stepsTaken[2].delay, 0.03 * F_CPU);
    EXPECT_EQ(stepsTaken[3].delay, 0.04 * F_CPU);
    EXPECT_EQ(stepsTaken[4].delay, 0.05 * F_CPU);
    EXPECT_EQ(stepsTaken[5].delay, 0.06 * F_CPU);
}

TEST_F(PathPlannerTest, WrapsStepListsCorrectly)
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

    auto& stepCommands = pru.pushedBlocks;

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

TEST_F(PathPlannerTest, SpecifiesCorrectBlockTimes)
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