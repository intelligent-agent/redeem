#pragma once
#include <cstdint>
#include <mutex>
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
    PathOptimizerType optimizer;
    std::vector<Path> queue;
    size_t writeIndex;
    size_t readIndex;
    size_t availableSlots;

public:
    PathQueue(size_t size)
        : optimizer(size)
        , queue(size)
        , writeIndex(0)
        , readIndex(0)
        , availableSlots(size)
    {
    }

    size_t availablePathSlots()
    {
        std::unique_lock<std::mutex> lock(mutex);

        return availableSlots;
    }

    void addPath(Path&& path)
    {
        std::unique_lock<std::mutex> lock(mutex);

        queueHasSpace.wait(lock, [this] { return availableSlots != 0; });

        queue[writeIndex] = std::move(path);
        writeIndex = (writeIndex + 1) % queue.size();
        availableSlots--;

        // subtract one because the optimizer does touch the last index
        optimizer.optimizeBackward(queue, readIndex, writeIndex - 1);

        if (availableSlots == queue.size() - 1)
        {
            lock.unlock();
            queueHasPaths.notify_all();
        }
    }

    Path popPath()
    {
        std::unique_lock<std::mutex> lock(mutex);

        queueHasPaths.wait(lock, [this] { return availableSlots != queue.size(); });

        const size_t currentReadIndex = readIndex;

        // subtract one because the optimizer does touch the last index
        optimizer.optimizeForward(queue, readIndex, writeIndex - 1);

        Path result(std::move(queue[currentReadIndex]));

        readIndex = (readIndex + 1) % queue.size();
        availableSlots++;

        if (availableSlots == 1)
        {
            lock.unlock();
            queueHasSpace.notify_all();
        }

        return std::move(result);
    }
};