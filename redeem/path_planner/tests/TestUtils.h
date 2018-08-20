#pragma once

#include <future>
#include <thread>

#include "Path.h"
#include "vectorN.h"

struct PathBuilder
{
    VectorN currentPosition;
    VectorN stepsPerM;
    VectorN maxSpeedJumps;
    VectorN maxSpeeds;
    VectorN maxAccelMPerSquareSecond;

    static PathBuilder CartesianBuilder()
    {
        return PathBuilder(VectorN(10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000),
            VectorN(0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01),
            VectorN(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
            VectorN(0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1));
    }

    static PathBuilder FullSpeedBuilder()
    {
        return PathBuilder(VectorN(10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000),
            VectorN(1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000),
            VectorN(1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000),
            VectorN(1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000));
    }

    PathBuilder()
    {
    }

    PathBuilder(const VectorN& stepsPerM, const VectorN& maxSpeedJumps, const VectorN& maxSpeeds, const VectorN& maxAccelMPerSquareSecond)
        : stepsPerM(stepsPerM)
        , maxSpeedJumps(maxSpeedJumps)
        , maxSpeeds(maxSpeeds)
        , maxAccelMPerSquareSecond(maxAccelMPerSquareSecond)
    {
    }

    Path makePath(double x, double y, double z, double speed)
    {
        Path result;

        VectorN travel(x, y, z, 0, 0, 0, 0, 0);

        VectorN endPosition = currentPosition + travel;

        result.initialize(
            (currentPosition * stepsPerM).round(), // machineStart
            (endPosition * stepsPerM).round(), // machineEnd
            currentPosition, // worldStart,
            endPosition, // worldEnd
            stepsPerM,
            maxSpeeds,
            maxAccelMPerSquareSecond,
            speed,
            std::numeric_limits<double>::infinity(),
            AXIS_CONFIG_XY,
            *(Delta*)nullptr,
            false,
            false);

        return result;
    }
};

template <typename T>
bool is_ready(std::future<T> const& future)
{
    return future.wait_for(std::chrono::seconds(0)) == std::future_status::ready;
}

struct WorkerThread
{
    std::promise<void> running;
    std::future<void> runningFuture;
    std::promise<void> finished;
    std::future<void> finishedFuture;

    std::thread thread;

    WorkerThread(std::function<void(void)> func)
        : running()
        , runningFuture(running.get_future())
        , finished()
        , finishedFuture(finished.get_future())
        , thread([this, func]() {
            running.set_value();
            func();
            finished.set_value();
        })
    {
        runningFuture.wait();
    }

    bool isFinished()
    {
        return is_ready(finishedFuture);
    }

    void waitAndJoin()
    {
        finishedFuture.wait();
        thread.join();
    }
};