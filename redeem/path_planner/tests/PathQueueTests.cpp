#define _SILENCE_TR1_NAMESPACE_DEPRECATION_WARNING

#include <future>

#include "gmock/gmock.h"
#include "gtest/gtest.h"

#include "PathQueue.h"

class DummyPathOptimizer : public PathOptimizerInterface
{
public:
    DummyPathOptimizer()
    {
    }

    void onPathAdded(std::vector<Path>&, size_t, size_t)
    {
    }

    void beforePathRemoval(std::vector<Path>&, size_t, size_t)
    {
    }
};

typedef PathQueue<DummyPathOptimizer> SimplePathQueue;

TEST(PathQueueBasics, ConstructsWithSize)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 15);
    EXPECT_EQ(queue.availablePathSlots(), 15);
}

TEST(PathQueueBasics, AcceptsPaths)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 15);
    Path path;
    queue.addPath(std::move(path));
    EXPECT_EQ(queue.availablePathSlots(), 14);
}

TEST(PathQueueBasics, ReturnsPaths)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 15);
    Path path;
    path.fixStartAndEndSpeed();
    queue.addPath(std::move(path));

    Path otherPath(queue.popPath());
    EXPECT_EQ(otherPath.isStartSpeedFixed(), true);
    EXPECT_EQ(queue.availablePathSlots(), 15);
}

TEST(PathQueueBasics, ReturnsPathsInOrder)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 15);
    Path path;
    path.fixStartAndEndSpeed();
    queue.addPath(std::move(path));

    path.zero();
    path.block();
    queue.addPath(std::move(path));

    EXPECT_EQ(queue.availablePathSlots(), 13);

    Path otherPath(queue.popPath());
    EXPECT_EQ(otherPath.isStartSpeedFixed(), true);

    otherPath.zero();

    otherPath = queue.popPath();
    EXPECT_EQ(otherPath.isStartSpeedFixed(), false);

    EXPECT_EQ(queue.availablePathSlots(), 15);
}

TEST(PathQueueBasics, WrapsAround)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 4);

    Path path;

    for (int i = 0; i < 60; i++)
    {
        queue.addPath(std::move(path));
        path = queue.popPath();
    }
}

template <typename T>
bool is_ready(std::future<T> const& future)
{
    return future.wait_for(std::chrono::seconds(0)) == std::future_status::ready;
}

TEST(PathQueueBasics, BlocksWhenFull)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 3);

    Path path;

    queue.addPath(std::move(path));
    path.zero();
    queue.addPath(std::move(path));
    path.zero();
    queue.addPath(std::move(path));

    std::promise<void> workerRunning;
    std::future<void> workerRunningFuture = workerRunning.get_future();
    std::promise<void> workerFinished;
    std::future<void> workerFinishedFuture = workerFinished.get_future();
    std::thread worker([&workerRunning, &workerFinished, &queue]() {
        Path path;
        workerRunning.set_value();
        queue.addPath(std::move(path));
        workerFinished.set_value();
    });

    workerRunningFuture.wait();

    EXPECT_EQ(is_ready(workerFinishedFuture), false);

    queue.popPath();

    workerFinishedFuture.wait();
    worker.join();
}

TEST(PathQueueBasics, BlocksWhenEmpty)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 3);

    std::promise<void> workerRunning;
    std::future<void> workerRunningFuture = workerRunning.get_future();
    std::promise<void> workerFinished;
    std::future<void> workerFinishedFuture = workerFinished.get_future();
    std::thread worker([&workerRunning, &workerFinished, &queue]() {
        workerRunning.set_value();
        queue.popPath();
        workerFinished.set_value();
    });

    workerRunningFuture.wait();

    EXPECT_EQ(is_ready(workerFinishedFuture), false);

    Path path;
    queue.addPath(std::move(path));

    workerFinishedFuture.wait();
    worker.join();
}

TEST(PathQueueBasics, BlocksUntilEmpty)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 4);

    Path path;
    queue.addPath(std::move(path));

    path.zero();
    queue.addPath(std::move(path));

    std::promise<void> workerRunning;
    std::future<void> workerRunningFuture = workerRunning.get_future();
    std::promise<void> workerFinished;
    std::future<void> workerFinishedFuture = workerFinished.get_future();
    std::thread worker([&workerRunning, &workerFinished, &queue]() {
        workerRunning.set_value();
        queue.waitForQueueToEmpty();
        workerFinished.set_value();
    });

    workerRunningFuture.wait();

    EXPECT_EQ(is_ready(workerFinishedFuture), false);

    path = queue.popPath();

    EXPECT_EQ(is_ready(workerFinishedFuture), false);

    path.zero();
    path = queue.popPath();

    workerFinishedFuture.wait();
    worker.join();
}

TEST(PathQueueBasics, AddsSyncEventToLastPathSinglePath)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 4);

    Path path;
    queue.addPath(std::move(path));

    queue.queueSyncEvent(false);

    Path result = queue.popPath();

    EXPECT_EQ(result.isSyncEvent(), true);
}

TEST(PathQueueBasics, AddsSyncEventToLastPathTwoPaths)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 4);

    Path path;
    queue.addPath(std::move(path));
    path.zero();
    queue.addPath(std::move(path));

    queue.queueSyncEvent(false);

    Path result = queue.popPath();
    EXPECT_EQ(result.isSyncEvent(), false);
    result.zero();
    result = queue.popPath();
    EXPECT_EQ(result.isSyncEvent(), true);
}

TEST(PathQueueBasics, AddsSyncEventToEmptyQueue)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 4);

    EXPECT_EQ(queue.availablePathSlots(), 4);

    queue.queueSyncEvent(false);

    ASSERT_EQ(queue.availablePathSlots(), 3);

    Path result = queue.popPath();
    EXPECT_EQ(result.isSyncEvent(), true);
    EXPECT_EQ(result.getDistance(), 0);
    EXPECT_EQ(result.getTimeInTicks(), 0);
}

TEST(PathQueueBasics, AddsSyncEventIfLastPathAlreadyIsOne)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 4);

    ASSERT_EQ(queue.availablePathSlots(), 4);

    queue.queueSyncEvent(false);

    ASSERT_EQ(queue.availablePathSlots(), 3);

    queue.queueSyncEvent(true);

    ASSERT_EQ(queue.availablePathSlots(), 2);

    Path result = queue.popPath();
    EXPECT_EQ(result.isSyncEvent(), true);
    EXPECT_EQ(result.getDistance(), 0);
    EXPECT_EQ(result.getTimeInTicks(), 0);

    result.zero();
    result = queue.popPath();
    EXPECT_EQ(result.isSyncWaitEvent(), true);
    EXPECT_EQ(result.getDistance(), 0);
    EXPECT_EQ(result.getTimeInTicks(), 0);
}

TEST(PathQueueBasics, AddsSyncWaitEventToLastPath)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 4);

    Path path;
    queue.addPath(std::move(path));

    queue.queueSyncEvent(true);

    Path result = queue.popPath();

    EXPECT_EQ(result.isSyncWaitEvent(), true);
}

class MockPathOptimizer : public PathOptimizerInterface
{
public:
    MOCK_METHOD3(onPathAdded, void(std::vector<Path>&, size_t, size_t));
    MOCK_METHOD3(beforePathRemoval, void(std::vector<Path>&, size_t, size_t));
};

typedef PathQueue<MockPathOptimizer> MockPathQueue;

TEST(PathQueueBasics, CallsOnPathAddedAfterAdd)
{
    MockPathOptimizer optimizer;
    MockPathQueue queue(optimizer, 4);

    Path path;

    EXPECT_CALL(optimizer, onPathAdded(::testing::_, 0, 0));

    queue.addPath(std::move(path));
}

TEST(PathQueueBasics, CallsBeforePathRemovalBeforePop)
{
    MockPathOptimizer optimizer;
    MockPathQueue queue(optimizer, 4);

    Path path;

    EXPECT_CALL(optimizer, onPathAdded(::testing::_, 0, 0));
    EXPECT_CALL(optimizer, beforePathRemoval(::testing::_, 0, 0));

    queue.addPath(std::move(path));
    path = queue.popPath();
}