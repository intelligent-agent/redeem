#include "PathOptimizer.h"

#include <cmath>

int64_t PathOptimizer::beforePathRemoval(std::vector<Path>& queue, PathQueueIndex first, PathQueueIndex last)
{
    int64_t timeChange = -queue[first.value].getEstimatedTime();

    if (first != last)
    {
        Path& firstPath = queue[first.value];
        Path& secondPath = queue[(first + 1).value];

        // Calculate the maximum possible end speed for firstPath.
        // We're using the formula vf^2 = v0^2 + 2*a*d.
        const double maximumEndSpeed = std::min(std::min(firstPath.getFullSpeed(), secondPath.getFullSpeed()),
            std::sqrt(firstPath.getStartSpeed() * firstPath.getStartSpeed() + firstPath.getAccelerationDistance2()));

        // The end speed was already set in the onPathAdded loop to be the maximum we could allow
        // while still decelerating when we run out of paths. We may need to lower it here to accelerate
        // properly, but we can't make it faster.
        const double newJunctionSpeed = std::min(maximumEndSpeed, firstPath.getEndSpeed());

        firstPath.setEndSpeed(newJunctionSpeed);
        secondPath.setStartSpeed(newJunctionSpeed);
        secondPath.setStartSpeedFixed(true);
    }

    return timeChange;
}

int64_t PathOptimizer::onPathAdded(std::vector<Path>& queue, PathQueueIndex first, PathQueueIndex last)
{
    calculateSafeSpeed(queue[last.value]);

    int64_t timeChange = queue[last.value].getEstimatedTime();

    if (first != last)
    {
        // compute the junction speed for the new path
        calculateJunctionSpeed(queue[(last - 1).value], queue[last.value]);
    }

    while (first != last)
    {
        // Loop through all paths in pairs and update the junctions between them.
        // This means we'll touch everything but the end speed of the last move (which is fixed at maxSpeedJump/2)
        // and the start speed of the first move (which is fixed because the move before that is already being carried out).
        Path& currentPath = queue[last.value];

        last--;
        Path& previousPath = queue[last.value];

        if (currentPath.getStartSpeed() == previousPath.getMaxJunctionSpeed())
        {
            break;
        }

        // Calculate the maximum possible start speed for currentPath.
        // We're using the formula vf^2 = v0^2 + 2*a*d, but we're working backwards.
        const double maximumStartSpeed = std::sqrt(currentPath.getEndSpeed() * currentPath.getEndSpeed() + currentPath.getAccelerationDistance2());

        const double newJunctionSpeed = std::min(maximumStartSpeed, previousPath.getMaxJunctionSpeed());

        if (newJunctionSpeed > currentPath.getStartSpeed())
        {
            currentPath.setStartSpeed(newJunctionSpeed);
            previousPath.setEndSpeed(newJunctionSpeed);
        }
        else
        {
            break;
        }
    }

    return timeChange;
}

void PathOptimizer::calculateJunctionSpeed(Path& previousPath, Path& newPath)
{
    double factor = 1;

    VectorN speedJumps = newPath.getSpeeds() - previousPath.getSpeeds();

    for (int i = 0; i < NUM_AXES; i++)
    {
        const double jump = std::abs(speedJumps[i]);

        if (jump > maxSpeedJumps[i])
        {
            factor = std::min(factor, maxSpeedJumps[i] / jump);
        }
    }

    const double junctionSpeed = std::min(previousPath.getFullSpeed() * factor, newPath.getFullSpeed());

    previousPath.setMaxJunctionSpeed(junctionSpeed);
}

void PathOptimizer::calculateSafeSpeed(Path& path)
{
    double safeTime = 0;

    for (int i = 0; i < NUM_AXES; i++)
    {
        const double safeAxisTime = std::abs(path.getWorldMove()[i]) / (maxSpeedJumps[i] / 2);
        assert(safeAxisTime >= 0);
        safeTime = std::max(safeTime, safeAxisTime);
    }

    const double safeSpeed = std::min(path.getDistance() / safeTime, path.getFullSpeed());

    path.setStartSpeed(safeSpeed);
    path.setEndSpeed(safeSpeed);
}

void PathOptimizer::setMaxSpeedJumps(const VectorN& maxSpeedJumps)
{
    this->maxSpeedJumps = maxSpeedJumps;
}
