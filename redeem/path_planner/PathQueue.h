#pragma once
#include <condition_variable>
#include <cstdint>
#include <mutex>
#if __has_include(<optional>)
#include <optional>
#else
#include <experimental/optional>
namespace std
{
using namespace experimental;
}
#endif
#include <vector>

#include "Logger.h"
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
    uint64_t maxTime;
    uint64_t curTime;
    size_t writeIndex;
    size_t readIndex;
    size_t availableSlots;
    bool running;

    bool doesQueueHaveSpace()
    {
        return availableSlots != 0 && curTime < maxTime;
    }

    bool addPathInternal(std::unique_lock<std::mutex>& lock, Path&& path)
    {
        static int logBlock = 10;
        bool logged = false;
        if (logBlock && !doesQueueHaveSpace())
        {
            LOGWARNING("path queue blocking - slots: " << availableSlots << "/" << queue.size() << " time: " << curTime << "/" << maxTime << std::endl);
            logBlock--;
            logged = true;
        }

        queueHasSpace.wait(lock, [this] { return !running || doesQueueHaveSpace(); });

        if (logged)
        {
            LOGWARNING("path queue has space again" << std::endl);
        }

        if (!running)
        {
            return false;
        }

        queue[writeIndex] = std::move(path);

        curTime += optimizer.onPathAdded(queue, readIndex, writeIndex);

        writeIndex = (writeIndex + 1) % queue.size();
        availableSlots--;

        if (availableSlots == queue.size() - 1)
        {
            queueHasPaths.notify_all();
        }

        return true;
    }

public:
    PathQueue(PathOptimizerType& optimizer, size_t size, uint64_t maxTime)
        : optimizer(optimizer)
        , queue(size)
        , maxTime(maxTime)
        , curTime(0)
        , writeIndex(0)
        , readIndex(0)
        , availableSlots(size)
        , running(true)
    {
    }

    uint64_t getQueuedMoveTime()
    {
        std::unique_lock<std::mutex> lock(mutex);

        return curTime;
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
        const bool addPathMightBeBlocking = !doesQueueHaveSpace();

        // subtract one because the optimizer does touch the last index
        curTime += optimizer.beforePathRemoval(queue, readIndex, (writeIndex + queue.size() - 1) % queue.size());

        readIndex = (readIndex + 1) % queue.size();
        availableSlots++;

        if (addPathMightBeBlocking && doesQueueHaveSpace())
        {
            queueHasSpace.notify_all();
        }

        if (availableSlots == queue.size())
        {
            LOGWARNING("Path queue underflow" << std::endl);
            queueIsEmpty.notify_all();
        }

        return std::move(queue[currentReadIndex]);
    }

    bool queueSyncEvent(SyncCallback& callback, bool blocking)
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
            lastPath.setSyncEvent(callback, blocking);
            return true;
        }
        else
        {
            Path dummyPath;
            dummyPath.setSyncEvent(callback, blocking);
            return addPathInternal(lock, std::move(dummyPath));
        }
    }

    bool queueWaitEvent(std::future<void>&& future)
    {
        std::unique_lock<std::mutex> lock(mutex);

        Path dummyPath;
        dummyPath.setWaitEvent(std::move(future));
        return addPathInternal(lock, std::move(dummyPath));
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
