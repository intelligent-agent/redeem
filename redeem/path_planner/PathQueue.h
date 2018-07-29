#pragma once
#include <condition_variable>
#include <cstdint>
#include <mutex>
#include <optional>
#include <vector>

#include "Path.h"
#include "PathOptimizerInterface.h"

template <typename PathOptimizerType, typename std::enable_if<std::is_base_of<PathOptimizerInterface, PathOptimizerType>::value>::type* = nullptr>
class PathQueue
{
private:
    std::mutex mutex;
    std::condition_variable queueHasPaths;
    std::condition_variable queueHasSpace;
    std::condition_variable queueIsEmpty;
    PathOptimizerType& optimizer;
    std::vector<Path> queue;
    size_t writeIndex;
    size_t readIndex;
    size_t availableSlots;
    bool running;

    bool addPathInternal(std::unique_lock<std::mutex>& lock, Path&& path)
    {
        queueHasSpace.wait(lock, [this] { return !running || availableSlots != 0; });

        if (!running)
        {
            return false;
        }

        queue[writeIndex] = std::move(path);
        writeIndex = (writeIndex + 1) % queue.size();
        availableSlots--;

        // subtract one because the optimizer does touch the last index
        optimizer.onPathAdded(queue, readIndex, writeIndex - 1);

        if (availableSlots == queue.size() - 1)
        {
            lock.unlock();
            queueHasPaths.notify_all();
        }

        return true;
    }

public:
    PathQueue(PathOptimizerType& optimizer, size_t size)
        : optimizer(optimizer)
        , queue(size)
        , writeIndex(0)
        , readIndex(0)
        , availableSlots(size)
        , running(true)
    {
    }

    size_t availablePathSlots()
    {
        std::unique_lock<std::mutex> lock(mutex);

        return availableSlots;
    }

    bool addPath(Path&& path)
    {
        std::unique_lock<std::mutex> lock(mutex);

        return addPathInternal(lock, std::move(path));
    }

    std::optional<Path> popPath()
    {
        std::unique_lock<std::mutex> lock(mutex);

        queueHasPaths.wait(lock, [this] { return !running || availableSlots != queue.size(); });

        if (!running)
        {
            return std::optional<Path>();
        }

        const size_t currentReadIndex = readIndex;

        // subtract one because the optimizer does touch the last index
        optimizer.beforePathRemoval(queue, readIndex, writeIndex - 1);

        Path result(std::move(queue[currentReadIndex]));

        readIndex = (readIndex + 1) % queue.size();
        availableSlots++;

        if (availableSlots == 1)
        {
            lock.unlock();
            queueHasSpace.notify_all();
        }
        else if (availableSlots == queue.size())
        {
            lock.unlock();
            queueIsEmpty.notify_all();
        }

        return std::move(result);
    }

    bool queueSyncEvent(bool blocking)
    {
        std::unique_lock<std::mutex> lock(mutex);

        if (!running)
        {
            return false;
        }

        const size_t lastPathIndex = (writeIndex + queue.size() - 1) % queue.size();

        if (queue.size() - availableSlots > 0
            && !queue[lastPathIndex].isSyncEvent()
            && !queue[lastPathIndex].isSyncWaitEvent())
        {
            Path& lastPath = queue[(writeIndex + queue.size() - 1) % queue.size()];
            lastPath.setSyncEvent(blocking);
            return true;
        }
        else
        {
            Path dummyPath;
            dummyPath.setSyncEvent(blocking);
            return addPathInternal(lock, std::move(dummyPath));
        }
    }

    bool waitForQueueToEmpty()
    {
        std::unique_lock<std::mutex> lock(mutex);

        queueIsEmpty.wait(lock, [this] { return !running || availableSlots == queue.size(); });

        return running;
    }

    void stop()
    {
        std::unique_lock<std::mutex> lock(mutex);

        running = false;

        queueHasPaths.notify_all();
        queueHasSpace.notify_all();
        queueIsEmpty.notify_all();
    }
};