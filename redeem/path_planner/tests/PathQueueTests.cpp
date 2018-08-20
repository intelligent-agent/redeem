#define _SILENCE_TR1_NAMESPACE_DEPRECATION_WARNING

#include <future>

#include "gmock/gmock.h"
#include "gtest/gtest.h"

#include "PathQueue.h"

#include "TestUtils.h"

class DummyPathOptimizer : public PathOptimizerInterface
{
public:
    DummyPathOptimizer()
    {
    }

    int64_t onPathAdded(std::vector<Path>& queue, size_t, size_t finish)
    {
        return queue[finish].getEstimatedTime();
    }

    int64_t beforePathRemoval(std::vector<Path>& queue, size_t start, size_t)
    {
        return -queue[start].getEstimatedTime();
    }
};

typedef PathQueue<DummyPathOptimizer> SimplePathQueue;

TEST(PathQueueBasics, ConstructsWithSize)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 15, 100);
    EXPECT_EQ(queue.availablePathSlots(), 15);
}

TEST(PathQueueBasics, AcceptsPaths)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 15, 100);
    Path path;
    ASSERT_TRUE(queue.addPath(std::move(path)));
    EXPECT_EQ(queue.availablePathSlots(), 14);
}

TEST(PathQueueBasics, ReturnsPaths)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 15, 100);
    Path path;
    path.fixStartAndEndSpeed();
    ASSERT_TRUE(queue.addPath(std::move(path)));

    Path otherPath(queue.popPath().value());
    EXPECT_EQ(otherPath.isStartSpeedFixed(), true);
    EXPECT_EQ(queue.availablePathSlots(), 15);
}

TEST(PathQueueBasics, ReturnsPathsInOrder)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 15, 100);
    Path path;
    path.fixStartAndEndSpeed();
    ASSERT_TRUE(queue.addPath(std::move(path)));

    path.zero();
    path.block();
    ASSERT_TRUE(queue.addPath(std::move(path)));

    EXPECT_EQ(queue.availablePathSlots(), 13);

    Path otherPath(queue.popPath().value());
    EXPECT_EQ(otherPath.isStartSpeedFixed(), true);

    otherPath.zero();

    otherPath = queue.popPath().value();
    EXPECT_EQ(otherPath.isStartSpeedFixed(), false);

    EXPECT_EQ(queue.availablePathSlots(), 15);
}

TEST(PathQueueBasics, WrapsAround)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 4, 100);

    Path path;

    for (int i = 0; i < 60; i++)
    {
        ASSERT_TRUE(queue.addPath(std::move(path)));
        path = queue.popPath().value();
    }
}

TEST(PathQueueBasics, BlocksWhenFull)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 3, 100);

    Path path;

    ASSERT_TRUE(queue.addPath(std::move(path)));
    path.zero();
    ASSERT_TRUE(queue.addPath(std::move(path)));
    path.zero();
    ASSERT_TRUE(queue.addPath(std::move(path)));

    WorkerThread thread([&queue]() {
        Path path;
        ASSERT_TRUE(queue.addPath(std::move(path)));
    });

    EXPECT_FALSE(thread.isFinished());

    queue.popPath();

    thread.waitAndJoin();
}

TEST(PathQueueBasics, BlocksWhenEmpty)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 3, 100);

    WorkerThread worker([&queue]() {
        queue.popPath();
    });

    EXPECT_FALSE(worker.isFinished());

    Path path;
    ASSERT_TRUE(queue.addPath(std::move(path)));

    worker.waitAndJoin();
}

TEST(PathQueueBasics, BlocksUntilEmpty)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 4, 100);

    Path path;
    ASSERT_TRUE(queue.addPath(std::move(path)));

    path.zero();
    ASSERT_TRUE(queue.addPath(std::move(path)));

    WorkerThread worker([&queue]() {
        queue.waitForQueueToEmpty();
    });

    EXPECT_FALSE(worker.isFinished());

    path = queue.popPath().value();

    EXPECT_FALSE(worker.isFinished());

    path.zero();
    path = queue.popPath().value();

    worker.waitAndJoin();
}

TEST(PathQueueBasics, AddsSyncEventToLastPathSinglePath)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 4, 100);

    Path path;
    ASSERT_TRUE(queue.addPath(std::move(path)));

    queue.queueSyncEvent(false);

    Path result = queue.popPath().value();

    EXPECT_EQ(result.isSyncEvent(), true);
}

TEST(PathQueueBasics, AddsSyncEventToLastPathTwoPaths)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 4, 100);

    Path path;
    ASSERT_TRUE(queue.addPath(std::move(path)));
    path.zero();
    ASSERT_TRUE(queue.addPath(std::move(path)));

    queue.queueSyncEvent(false);

    Path result = queue.popPath().value();
    EXPECT_EQ(result.isSyncEvent(), false);
    result.zero();
    result = queue.popPath().value();
    EXPECT_EQ(result.isSyncEvent(), true);
}

TEST(PathQueueBasics, AddsSyncEventToEmptyQueue)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 4, 100);

    EXPECT_EQ(queue.availablePathSlots(), 4);

    queue.queueSyncEvent(false);

    ASSERT_EQ(queue.availablePathSlots(), 3);

    Path result = queue.popPath().value();
    EXPECT_EQ(result.isSyncEvent(), true);
    EXPECT_EQ(result.getDistance(), 0);
    EXPECT_EQ(result.getEstimatedTime(), 0);
}

TEST(PathQueueBasics, AddsSyncEventIfLastPathAlreadyIsOne)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 4, 100);

    ASSERT_EQ(queue.availablePathSlots(), 4);

    queue.queueSyncEvent(false);

    ASSERT_EQ(queue.availablePathSlots(), 3);

    queue.queueSyncEvent(true);

    ASSERT_EQ(queue.availablePathSlots(), 2);

    Path result = queue.popPath().value();
    EXPECT_EQ(result.isSyncEvent(), true);
    EXPECT_EQ(result.getDistance(), 0);
    EXPECT_EQ(result.getEstimatedTime(), 0);

    result.zero();
    result = queue.popPath().value();
    EXPECT_EQ(result.isSyncWaitEvent(), true);
    EXPECT_EQ(result.getDistance(), 0);
    EXPECT_EQ(result.getEstimatedTime(), 0);
}

TEST(PathQueueBasics, AddsSyncWaitEventToLastPath)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 4, 100);

    Path path;
    ASSERT_TRUE(queue.addPath(std::move(path)));

    queue.queueSyncEvent(true);

    Path result = queue.popPath().value();

    EXPECT_EQ(result.isSyncWaitEvent(), true);
}

TEST(PathQueueBasics, FailsToPopWhenStopping)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 4, 100);

    queue.stop();

    auto result = queue.popPath();

    EXPECT_EQ(result.has_value(), false);
}

TEST(PathQueueBasics, FailsToAddWhenStopping)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 4, 100);

    queue.stop();

    Path path;
    EXPECT_EQ(queue.addPath(std::move(path)), false);
}

TEST(PathQueueBasics, StopsBlockingAddWhenStopping)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 2, 100);

    Path path;
    ASSERT_TRUE(queue.addPath(std::move(path)));

    path.zero();
    ASSERT_TRUE(queue.addPath(std::move(path)));

    ASSERT_EQ(queue.availablePathSlots(), 0);

    WorkerThread worker([&queue]() {
        Path path;
        ASSERT_FALSE(queue.addPath(std::move(path)));
    });

    EXPECT_FALSE(worker.isFinished());

    queue.stop();

    worker.waitAndJoin();
}

TEST(PathQueueBasics, StopsBlockingPopWhenStopping)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 2, 100);

    WorkerThread worker([&queue]() {
        queue.popPath();
    });

    EXPECT_FALSE(worker.isFinished());

    queue.stop();

    worker.waitAndJoin();
}

TEST(PathQueueBasics, FailsToQueueSyncEventWhenStopping)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 4, 100);

    queue.stop();
    EXPECT_EQ(queue.queueSyncEvent(false), false);
}

TEST(PathQueueBasics, FailsToWaitForEmptyWhenStopping)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 4, 100);

    queue.stop();
    EXPECT_EQ(queue.waitForQueueToEmpty(), false);
}

TEST(PathQueueBasics, StopsBlockingWaitForEmptyWhenStopping)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 4, 100);

    Path path;
    ASSERT_EQ(queue.addPath(std::move(path)), true);

    WorkerThread worker([&queue]() {
        queue.waitForQueueToEmpty();
    });

	EXPECT_FALSE(worker.isFinished());

    queue.stop();

    worker.waitAndJoin();
}

TEST(PathQueueBasics, FailsToQueueSyncEventWhenFullAndStopping)
{
    DummyPathOptimizer optimizer;
    SimplePathQueue queue(optimizer, 1, 100);

    Path path;
    path.setSyncEvent(true);
    ASSERT_TRUE(queue.addPath(std::move(path)));

    WorkerThread worker([&queue]() {
        EXPECT_FALSE(queue.queueSyncEvent(false));
    });

	EXPECT_FALSE(worker.isFinished());

    queue.stop();

    worker.waitAndJoin();
}

class MockPathOptimizer : public PathOptimizerInterface
{
public:
    MOCK_METHOD3(onPathAdded, int64_t(std::vector<Path>&, size_t, size_t));
    MOCK_METHOD3(beforePathRemoval, int64_t(std::vector<Path>&, size_t, size_t));
};

typedef PathQueue<MockPathOptimizer> MockPathQueue;

TEST(PathQueueBasics, BlocksWhenFullByTime)
{
    MockPathOptimizer optimizer;
    MockPathQueue queue(optimizer, 10, 30ll * F_CPU);

	Path path;
    EXPECT_CALL(optimizer, onPathAdded(::testing::_, 0, 0)).WillOnce(::testing::Return(31ll * F_CPU));
    queue.addPath(std::move(path));

	EXPECT_CALL(optimizer, onPathAdded);
    EXPECT_CALL(optimizer, beforePathRemoval).WillOnce(::testing::Return(-31ll * F_CPU));

    WorkerThread thread([&queue]() {
        Path path;
        EXPECT_TRUE(queue.addPath(std::move(path)));
    });

    EXPECT_FALSE(thread.isFinished());

    queue.popPath();

    thread.waitAndJoin();
}


TEST(PathQueueBasics, CallsOnPathAddedAfterAdd)
{
    MockPathOptimizer optimizer;
    MockPathQueue queue(optimizer, 4, 100);

    Path path;

    EXPECT_CALL(optimizer, onPathAdded(::testing::_, 0, 0));

    ASSERT_TRUE(queue.addPath(std::move(path)));
}

TEST(PathQueueBasics, CallsBeforePathRemovalBeforePop)
{
    MockPathOptimizer optimizer;
    MockPathQueue queue(optimizer, 4, 100);

    Path path;

    EXPECT_CALL(optimizer, onPathAdded(::testing::_, 0, 0));
    EXPECT_CALL(optimizer, beforePathRemoval(::testing::_, 0, 0));

    ASSERT_TRUE(queue.addPath(std::move(path)));
    path = queue.popPath().value();
}

TEST(PathQueueBasics, HandlesWrapAroundForOnPathAdded)
{
    MockPathOptimizer optimizer;
    MockPathQueue queue(optimizer, 3, 100);

    Path path;

    EXPECT_CALL(optimizer, onPathAdded(::testing::_, 0, 0));
    EXPECT_CALL(optimizer, onPathAdded(::testing::_, 0, 1));
    EXPECT_CALL(optimizer, beforePathRemoval(::testing::_, 0, 1));
    EXPECT_CALL(optimizer, onPathAdded(::testing::_, 1, 2));
    EXPECT_CALL(optimizer, onPathAdded(::testing::_, 1, 0));

    ASSERT_TRUE(queue.addPath(std::move(path)));
    ASSERT_TRUE(queue.addPath(std::move(path)));
    ASSERT_TRUE(queue.popPath());
    ASSERT_TRUE(queue.addPath(std::move(path)));
    ASSERT_TRUE(queue.addPath(std::move(path)));
}

TEST(PathQueueBasics, HandlesWrapAroundForBeforePathRemoval)
{
    MockPathOptimizer optimizer;
    MockPathQueue queue(optimizer, 3, 100);

    Path path;

    EXPECT_CALL(optimizer, onPathAdded(::testing::_, 0, 0));
    EXPECT_CALL(optimizer, onPathAdded(::testing::_, 0, 1));
    EXPECT_CALL(optimizer, onPathAdded(::testing::_, 0, 2));
    EXPECT_CALL(optimizer, beforePathRemoval(::testing::_, 0, 2));
    EXPECT_CALL(optimizer, beforePathRemoval(::testing::_, 1, 2));
    EXPECT_CALL(optimizer, onPathAdded(::testing::_, 2, 0));
    EXPECT_CALL(optimizer, beforePathRemoval(::testing::_, 2, 0));
    EXPECT_CALL(optimizer, beforePathRemoval(::testing::_, 0, 0));

    ASSERT_TRUE(queue.addPath(std::move(path)));
    ASSERT_TRUE(queue.addPath(std::move(path)));
    ASSERT_TRUE(queue.addPath(std::move(path)));
    ASSERT_TRUE(queue.popPath());
    ASSERT_TRUE(queue.popPath());
    ASSERT_TRUE(queue.addPath(std::move(path)));
    ASSERT_TRUE(queue.popPath());
    ASSERT_TRUE(queue.popPath());
}