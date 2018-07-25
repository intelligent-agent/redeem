#include "PathOptimizer.h"

void PathOptimizer::optimizeForward(std::vector<Path>& queue, size_t first, size_t last)
{
    double leftSpeed = 0;

    while (first != last)
    { // All except last segment, which has fixed end speed
        Path& currentPath = queue[first];
        first = (first + 1) % queue.size();
        Path& nextPath = queue[first];

        leftSpeed = nextPath.getStartSpeed();

        // Avoid speed calcs if we know we can accelerate within the line.
        double vmaxRight = (currentPath.willMoveReachFullSpeed() ? currentPath.getFullSpeed() : sqrt(leftSpeed * leftSpeed + currentPath.getAccelerationDistance2()));
        if (vmaxRight > currentPath.getEndSpeed())
        { // Could be higher next run?
            if (leftSpeed < currentPath.getMinSpeed())
            {
                leftSpeed = currentPath.getMinSpeed();
                currentPath.setEndSpeed(sqrt(leftSpeed * leftSpeed + currentPath.getAccelerationDistance2()));
            }
            currentPath.setStartSpeed(leftSpeed);

            leftSpeed = std::max(std::min(currentPath.getEndSpeed(), currentPath.getMaxJunctionSpeed()), nextPath.getMinSpeed());
            nextPath.setStartSpeed(leftSpeed);
            if (currentPath.getEndSpeed() == currentPath.getMaxJunctionSpeed())
            { // Full speed reached, don't compute again!
                currentPath.setEndSpeedFixed(true);
                nextPath.setStartSpeedFixed(true);
            }
            currentPath.invalidateStepperPathParameters();
        }
        else
        { // We can accelerate full speed without reaching limit, which is as fast as possible. Fix it!
            currentPath.fixStartAndEndSpeed();
            currentPath.invalidateStepperPathParameters();
            if (currentPath.getMinSpeed() > leftSpeed)
            {
                leftSpeed = currentPath.getMinSpeed();
                vmaxRight = sqrt(leftSpeed * leftSpeed + currentPath.getAccelerationDistance2());
            }
            currentPath.setStartSpeed(leftSpeed);
            currentPath.setEndSpeed(std::max(currentPath.getMinSpeed(), vmaxRight));

            leftSpeed = std::max(std::min(currentPath.getEndSpeed(), currentPath.getMaxJunctionSpeed()), nextPath.getMinSpeed());
            nextPath.setStartSpeed(leftSpeed);
            nextPath.setStartSpeedFixed(true);
        }
    }

    Path& lastPath = queue[last];
    lastPath.setStartSpeed(std::max(lastPath.getMinSpeed(), leftSpeed)); // This is the new segment, which is updated anyway, no extra flag needed.
}

void PathOptimizer::optimizeBackward(std::vector<Path>& queue, size_t first, size_t last)
{
    // Last element is already fixed in start speed
    while (first != last)
    {
        Path& currentPath = queue[last];

        last = (last + queue.size() - 1) % queue.size();
        Path& previousPath = queue[last];

        double lastJunctionSpeed = currentPath.getEndSpeed(); // Start always with safe speed

        // Avoid speed calcs if we know we can accelerate within the line
        // acceleration is acceleration*distance*2! What can be reached if we try?
        lastJunctionSpeed = (currentPath.willMoveReachFullSpeed() ? currentPath.getFullSpeed() : sqrt(lastJunctionSpeed * lastJunctionSpeed + currentPath.getAccelerationDistance2()));
        // If that speed is more that the maximum junction speed allowed then ...
        if (lastJunctionSpeed >= previousPath.getMaxJunctionSpeed())
        { // Limit is reached
            // If the previousPath line's end speed has not been updated to maximum speed then do it now
            if (previousPath.getEndSpeed() != previousPath.getMaxJunctionSpeed())
            {
                previousPath.invalidateStepperPathParameters(); // Needs recomputation
                previousPath.setEndSpeed(std::max(previousPath.getMinSpeed(), previousPath.getMaxJunctionSpeed())); // possibly unneeded???
            }
            // If actual line start speed has not been updated to maximum speed then do it now
            if (currentPath.getStartSpeed() != previousPath.getMaxJunctionSpeed())
            {
                currentPath.setStartSpeed(std::max(currentPath.getMinSpeed(), previousPath.getMaxJunctionSpeed())); // possibly unneeded???
                currentPath.invalidateStepperPathParameters();
            }
            lastJunctionSpeed = previousPath.getEndSpeed();
        }
        else
        {
            // Block prev end and currentPath start as calculated speed and recalculate plateau speeds (which could move the speed higher again)
            currentPath.setStartSpeed(std::max(currentPath.getMinSpeed(), lastJunctionSpeed));
            lastJunctionSpeed = std::max(lastJunctionSpeed, previousPath.getMinSpeed());
            previousPath.setEndSpeed(lastJunctionSpeed);
            previousPath.invalidateStepperPathParameters();
            currentPath.invalidateStepperPathParameters();
        }
    } // while loop
}