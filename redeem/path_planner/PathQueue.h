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
    std::recursive_mutex mutex;
    std::condition_variable_any queueHasPaths;
    std::condition_variable_any queueHasSpace;
    std::condition_variable_any queueIsEmpty;
    PathOptimizerType& optimizer;
    std::vector<Path> queue;
    size_t writeIndex;
    size_t readIndex;
    size_t availableSlots;

public:
    PathQueue(PathOptimizerType& optimizer, size_t size)
        : optimizer(optimizer)
        , queue(size)
        , writeIndex(0)
        , readIndex(0)
        , availableSlots(size)
    {
    }

    size_t availablePathSlots()
    {
        std::unique_lock<std::recursive_mutex> lock(mutex);

        return availableSlots;
    }

    void addPath(Path&& path)
    {
        std::unique_lock<std::recursive_mutex> lock(mutex);

        queueHasSpace.wait(lock, [this] { return availableSlots != 0; });

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
    }

    Path popPath()
    {
        std::unique_lock<std::recursive_mutex> lock(mutex);

        queueHasPaths.wait(lock, [this] { return availableSlots != queue.size(); });

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

    void queueSyncEvent(bool blocking)
    {
        std::unique_lock<std::recursive_mutex> lock(mutex);

        const size_t lastPathIndex = (writeIndex + queue.size() - 1) % queue.size();

        if (queue.size() - availableSlots > 0
            && !queue[lastPathIndex].isSyncEvent()
            && !queue[lastPathIndex].isSyncWaitEvent())
        {
            Path& lastPath = queue[(writeIndex + queue.size() - 1) % queue.size()];
            lastPath.setSyncEvent(blocking);
        }
        else
        {
            Path dummyPath;
            dummyPath.setSyncEvent(blocking);
            addPath(std::move(dummyPath));
        }
    }

    void waitForQueueToEmpty()
    {
        std::unique_lock<std::recursive_mutex> lock(mutex);

        queueIsEmpty.wait(lock, [this] { return availableSlots == queue.size(); });
    }
};