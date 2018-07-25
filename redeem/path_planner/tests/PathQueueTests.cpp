#define _SILENCE_TR1_NAMESPACE_DEPRECATION_WARNING

#include <future>

#include "gmock/gmock.h"
#include "gtest/gtest.h"

#include "PathQueue.h"

class DummyPathOptimizer : public PathOptimizerInterface
{
public:
    DummyPathOptimizer(size_t)
    {
    }

    void optimizeBackward(std::vector<Path>&, size_t, size_t)
    {
    }

    void optimizeForward(std::vector<Path>&, size_t, size_t)
    {
    }
};

typedef PathQueue<DummyPathOptimizer> SimplePathQueue;

TEST(PathQueueBasics, ConstructsWithSize)
{
    SimplePathQueue queue(15);
    EXPECT_EQ(queue.availablePathSlots(), 15);
}

TEST(PathQueueBasics, AcceptsPaths)
{
    SimplePathQueue queue(15);
    Path path;
    queue.addPath(std::move(path));
    EXPECT_EQ(queue.availablePathSlots(), 14);
}

TEST(PathQueueBasics, ReturnsPaths)
{
    SimplePathQueue queue(15);
    Path path;
    path.fixStartAndEndSpeed();
    queue.addPath(std::move(path));

    Path otherPath(queue.popPath());
    EXPECT_EQ(otherPath.isStartSpeedFixed(), true);
    EXPECT_EQ(queue.availablePathSlots(), 15);
}

TEST(PathQueueBasics, ReturnsPathsInOrder)
{
    SimplePathQueue queue(15);
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
    SimplePathQueue queue(4);

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
    SimplePathQueue queue(3);

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
    SimplePathQueue queue(3);

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

class MockPathOptimizer : public PathOptimizerInterface
{
private:
    static MockPathOptimizer* singleton;

public:
    MockPathOptimizer(size_t)
    {
        singleton = this;
    }

    MOCK_METHOD3(optimizeBackward, void(std::vector<Path>&, size_t, size_t));
    MOCK_METHOD3(optimizeForward, void(std::vector<Path>&, size_t, size_t));

    static MockPathOptimizer& get()
    {
        return *singleton;
    }
};

MockPathOptimizer* MockPathOptimizer::singleton = nullptr;

typedef PathQueue<MockPathOptimizer> MockPathQueue;

TEST(PathQueueBasics, CallsBackwardOptimizerAfterAdd)
{
    MockPathQueue queue(4);

    Path path;

    EXPECT_CALL(MockPathOptimizer::get(), optimizeBackward(::testing::_, 0, 0));

    queue.addPath(std::move(path));
}

TEST(PathQueueBasics, CallsForwardOptimizerAfterPop)
{
    MockPathQueue queue(4);

    Path path;

    EXPECT_CALL(MockPathOptimizer::get(), optimizeForward(::testing::_, 0, 0));

    queue.addPath(std::move(path));
    path = queue.popPath();
}