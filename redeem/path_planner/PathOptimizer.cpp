#include "PathOptimizer.h"

void PathOptimizer::beforePathRemoval(std::vector<Path>& queue, size_t first, size_t last)
{
    double leftSpeed = 0;

    if (first != last)
    {
        Path& firstPath = queue[first];
        Path& secondPath = queue[(first + 1) % queue.size()];

        // Calculate the maximum possible end speed for firstPath.
        // We're using the formula vf^2 = v0^2 + 2*a*d.
        const double maximumEndSpeed = std::sqrt(firstPath.getStartSpeed() * firstPath.getStartSpeed() + firstPath.getAccelerationDistance2());

        const double newJunctionSpeed = std::min(maximumEndSpeed, firstPath.getMaxJunctionSpeed());

        firstPath.setEndSpeed(maximumEndSpeed);
        secondPath.setStartSpeed(maximumEndSpeed);
        secondPath.setStartSpeedFixed(true);
    }
}

void PathOptimizer::onPathAdded(std::vector<Path>& queue, size_t first, size_t last)
{
    while (first != last)
    {
        // Loop through all paths in pairs and update the junctions between them.
        // This means we'll touch everything but the end speed of the last move (which is fixed at maxSpeedJump/2)
        // and the start speed of the first move (which is fixed because the move before that is already being carried out).
        Path& currentPath = queue[last];

        last = (last + queue.size() - 1) % queue.size();
        Path& previousPath = queue[last];

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
}