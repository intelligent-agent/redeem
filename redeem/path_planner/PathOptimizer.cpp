#include "PathOptimizer.h"

#include <cmath>
#include <tuple>

void sanityCheckStartAndEndSpeeds(double startSpeed, double endSpeed, double distance, double accel)
{
    double maxReachableEndSpeed = std::sqrt(startSpeed * startSpeed + 2 * accel * distance);
    double minReachableEndSpeed = std::sqrt(startSpeed * startSpeed - 2 * accel * distance);

    double maxReachableStartSpeed = std::sqrt(endSpeed * endSpeed + 2 * accel * distance);
    double minReachableStartSpeed = std::sqrt(endSpeed * endSpeed - 2 * accel * distance);

    assert(APPROX_GREATER_THAN(endSpeed, minReachableEndSpeed) || std::isnan(minReachableEndSpeed));
    assert(APPROX_LESS_THAN(endSpeed, maxReachableEndSpeed) || std::isnan(maxReachableEndSpeed));
    assert(APPROX_GREATER_THAN(startSpeed, minReachableStartSpeed) || std::isnan(minReachableStartSpeed));
    assert(APPROX_LESS_THAN(startSpeed, maxReachableStartSpeed) || std::isnan(maxReachableStartSpeed));
}

void sanityCheckPathSpeeds(const Path& path)
{
    sanityCheckStartAndEndSpeeds(path.getStartSpeed(), path.getEndSpeed(), path.getDistance(), path.getAcceleration());
}

int64_t PathOptimizer::beforePathRemoval(std::vector<Path>& queue, PathQueueIndex first, PathQueueIndex last)
{
    int64_t timeChange = -queue[first.value].getEstimatedTime();

    if (first != last)
    {
        Path& firstPath = queue[first.value];
        Path& secondPath = queue[(first + 1).value];

        // Calculate the maximum possible end speed for firstPath.
        // We're using the formula vf^2 = v0^2 + 2*a*d.
        const double maximumEndSpeed = std::min(firstPath.getFullSpeed(),
            std::sqrt(firstPath.getStartSpeed() * firstPath.getStartSpeed() + firstPath.getAccelerationDistance2()));

        // The end speed was already set in the onPathAdded loop to be the maximum we could allow
        // while still decelerating when we run out of paths. We may need to lower it here to accelerate
        // properly, but we can't make it faster.
        const double newEndSpeed = std::min(maximumEndSpeed, firstPath.getEndSpeed());

        firstPath.setEndSpeed(newEndSpeed);
        sanityCheckPathSpeeds(firstPath);

        double maxStartSpeed = calculateReachableJunctionSpeed(firstPath, newEndSpeed, secondPath);
        secondPath.setStartSpeed(std::min(secondPath.getStartSpeed(), maxStartSpeed));
        secondPath.setStartSpeedFixed(true);
    }

    return timeChange;
}

int64_t PathOptimizer::onPathAdded(std::vector<Path>& queue, PathQueueIndex first, PathQueueIndex last)
{
    Path& newPath = queue[last.value];

    {
        const double safeSpeed = calculateSafeSpeed(newPath);
        newPath.setStartSpeed(safeSpeed);
        newPath.setEndSpeed(safeSpeed);
        sanityCheckPathSpeeds(newPath);
    }

    int64_t timeChange = newPath.getEstimatedTime();

    if (first != last)
    {
        // compute the junction speed for the new path
        Path& previousPath = queue[(last - 1).value];

        double junctionEntrySpeed = 0, junctionExitSpeed = 0;
        std::tie(junctionEntrySpeed, junctionExitSpeed) = calculateJunctionSpeed(previousPath, newPath);
        previousPath.setMaxEndSpeed(junctionEntrySpeed);
        newPath.setMaxStartSpeed(junctionExitSpeed);
    }

    bool firstIteration = true;

    while (first != last)
    {
        // Loop through all paths in pairs and update the junctions between them.
        // This means we'll touch everything but the end speed of the last move (which is fixed at maxSpeedJump/2)
        // and the start speed of the first move (which is fixed because the move before that is already being carried out).
        Path& currentPath = queue[last.value];

        last--;
        Path& previousPath = queue[last.value];

        // Normally, this would mean there's no further improvement to make on this path or any before it.
        // The exception is when we've just added a path with speeds below maxSpeedJump, so it has
        // speeds maxed out when it's added. In this case, force the loop to continue because the path before
        // it may be able to raise its junction entry speed.
        if (currentPath.getStartSpeed() == currentPath.getMaxStartSpeed() && !firstIteration)
        {
            break;
        }

        // Calculate the maximum possible start speed for currentPath.
        // We're using the formula vf^2 = v0^2 + 2*a*d, but we're working backwards.
        const double maximumStartSpeed = std::sqrt(currentPath.getEndSpeed() * currentPath.getEndSpeed() + currentPath.getAccelerationDistance2());

        const double newStartSpeed = std::min(maximumStartSpeed, currentPath.getMaxStartSpeed());

        // Same reasoning as above - the first iteration is special
        if (newStartSpeed > currentPath.getStartSpeed() || firstIteration)
        {
            currentPath.setStartSpeed(newStartSpeed);
            const double newEndSpeed = calculateReachableJunctionSpeed(currentPath, newStartSpeed, previousPath);
            previousPath.setEndSpeed(std::min(newEndSpeed, previousPath.getMaxEndSpeed()));

            // sanity check - if our current path is hittings its max start speed, the previous path
            // must also hit its max end speed
            if (APPROX_EQUAL(currentPath.getStartSpeed(), currentPath.getMaxStartSpeed()))
            {
                APPROX_EQUAL(previousPath.getEndSpeed(), previousPath.getMaxEndSpeed());
            }

            // Note that the opposite isn't necessarily true - this loop only promises that moves can decelerate within
            // limits, not that they can accelerate within limits.
        }
        else
        {
            break;
        }

        firstIteration = false;
    }

    return timeChange;
}

bool PathOptimizer::doesJunctionSpeedViolateMaxSpeedJumps(const VectorN& entrySpeeds, const VectorN& exitSpeeds)
{
    const VectorN speedJumps = entrySpeeds - exitSpeeds;

    bool areSpeedsOkay = true;

    for (int i = 0; i < NUM_AXES; i++)
    {
        areSpeedsOkay &= std::abs(speedJumps[i]) - maxSpeedJumps[i] < NEGLIGIBLE_ERROR;
    }

    return !areSpeedsOkay;
}

std::tuple<double, double> PathOptimizer::calculateJunctionSpeed(const Path& entryPath, const Path& exitPath)
{
    double entryFactor = 1;
    double exitFactor = 1;

    const VectorN exitPathSpeeds = exitPath.getSpeeds();
    const VectorN entryPathSpeeds = entryPath.getSpeeds();

    const VectorN speedJumps = exitPath.getSpeeds() - entryPath.getSpeeds();

    // First try the fancy algorithm. This works very well for single or mostly-single axis moves,
    // but can fail to find a correct result for more complex moves.
    for (int i = 0; i < NUM_AXES; i++)
    {
        const double jump = speedJumps[i];

        if (std::abs(jump) > maxSpeedJumps[i])
        {
            const double desiredEntryAxisSpeed = entryPath.getSpeeds()[i];
            const double desiredExitAxisSpeed = exitPath.getSpeeds()[i];

            // three cases - stop, reversal, normal
            // first check for a stop - if so, slow down move where this axis actually moves
            if (desiredEntryAxisSpeed == 0)
            {
                exitFactor = std::min(exitFactor, maxSpeedJumps[i] / std::abs(desiredExitAxisSpeed));
            }
            else if (desiredExitAxisSpeed == 0)
            {
                entryFactor = std::min(entryFactor, maxSpeedJumps[i] / std::abs(desiredEntryAxisSpeed));
            }
            else if (std::signbit(desiredEntryAxisSpeed) != std::signbit(desiredExitAxisSpeed))
            {
                // reversal case
                // first try to slow down the faster move in absolute terms
                if (std::abs(desiredEntryAxisSpeed) > std::abs(desiredExitAxisSpeed) && std::abs(desiredExitAxisSpeed) <= 0.5 * maxSpeedJumps[i])
                {
                    // entry is faster than exit and slowing it down won't make it slower than exit
                    // slow down the entry speed
                    const double possibleEntryAxisSpeed = desiredExitAxisSpeed + (desiredEntryAxisSpeed > 0) ? maxSpeedJumps[i] : -maxSpeedJumps[i];
                    entryFactor = std::min(entryFactor, possibleEntryAxisSpeed / desiredEntryAxisSpeed);
                }
                else if (std::abs(desiredExitAxisSpeed) > std::abs(desiredEntryAxisSpeed) && std::abs(desiredEntryAxisSpeed) <= 0.5 * maxSpeedJumps[i])
                {
                    // exit is faster than entry and slowing it down won't make it slower than entry
                    // slow down the exit speed
                    const double possibleExitAxisSpeed = desiredEntryAxisSpeed + (desiredExitAxisSpeed > 0) ? maxSpeedJumps[i] : -maxSpeedJumps[i];
                    exitFactor = std::min(exitFactor, possibleExitAxisSpeed / desiredExitAxisSpeed);
                }
                else
                {
                    // we need to slow down both - use the safe speeds
                    entryFactor = std::min(entryFactor, std::abs((0.5 * maxSpeedJumps[i]) / desiredEntryAxisSpeed));
                    exitFactor = std::min(exitFactor, std::abs((0.5 * maxSpeedJumps[i]) / desiredExitAxisSpeed));
                }
            }
            else
            {
                // normal case - same direction, just accelerating or decelerating
                // slow down the faster move
                if (std::abs(desiredEntryAxisSpeed) > std::abs(desiredExitAxisSpeed))
                {
                    const double possibleEntryAxisSpeed = desiredEntryAxisSpeed > 0 ? desiredExitAxisSpeed + maxSpeedJumps[i]
                                                                                    : desiredExitAxisSpeed - maxSpeedJumps[i];
                    entryFactor = std::min(entryFactor, possibleEntryAxisSpeed / desiredEntryAxisSpeed);
                }
                else
                {
                    const double possibleExitAxisSpeed = desiredExitAxisSpeed > 0 ? desiredEntryAxisSpeed + maxSpeedJumps[i]
                                                                                  : desiredEntryAxisSpeed - maxSpeedJumps[i];
                    exitFactor = std::min(exitFactor, possibleExitAxisSpeed / desiredExitAxisSpeed);
                }
            }
        }
    }

    const double entrySafeSpeed = calculateSafeSpeed(entryPath);
    const double exitSafeSpeed = calculateSafeSpeed(exitPath);

    // Check if it worked
    if (doesJunctionSpeedViolateMaxSpeedJumps(entryPath.getSpeeds() * entryFactor, exitPath.getSpeeds() * exitFactor))
    {
        // fallback strategy
        double factor = 1;

        for (int i = 0; i < NUM_AXES; i++)
        {
            const double jump = std::abs(speedJumps[i]);

            if (jump > maxSpeedJumps[i])
            {
                factor = std::min(factor, maxSpeedJumps[i] / jump);
            }
        }

        entryFactor = exitFactor = factor;
    }

    double entrySpeed = entryPath.getFullSpeed() * entryFactor;
    double exitSpeed = exitPath.getFullSpeed() * exitFactor;

    // one last tweak - if the safe speeds are higher than these, we want to use those instead'
    if (entrySafeSpeed > entrySpeed || exitSafeSpeed > exitSpeed)
    {
        entryFactor = entrySafeSpeed / entryPath.getFullSpeed();
        exitFactor = exitSafeSpeed / exitPath.getFullSpeed();
        entrySpeed = entrySafeSpeed;
        exitSpeed = exitSafeSpeed;
    }

    assert(entryFactor >= 0);
    assert(exitFactor >= 0);
    assert(entrySpeed >= entrySafeSpeed);
    assert(exitSpeed >= exitSafeSpeed);

    assert(!doesJunctionSpeedViolateMaxSpeedJumps(entryPath.getSpeeds() * entryFactor, exitPath.getSpeeds() * exitFactor));

    return std::tuple<double, double>(entrySpeed, exitSpeed);
}

double PathOptimizer::calculateReachableJunctionSpeed(const Path& firstPath, const double firstJunctionSpeed, const Path& secondPath)
{
    if (secondPath.getDistance() == 0)
    {
        return 0;
    }

    const VectorN firstJunctionSpeeds = firstJunctionSpeed != 0
        ? firstPath.getSpeeds() * (firstJunctionSpeed / firstPath.getFullSpeed())
        : VectorN();
    const VectorN speedJumps = firstJunctionSpeeds - secondPath.getSpeeds();

    double secondFactor = 1.0;

    for (int i = 0; i < NUM_AXES; i++)
    {
        if (std::abs(speedJumps[i]) > maxSpeedJumps[i])
        {
            double reachableSpeed = firstJunctionSpeeds[i] + (secondPath.getSpeeds()[i] > firstJunctionSpeeds[i] ? maxSpeedJumps[i] : -maxSpeedJumps[i]);

            // tweak for numerical accuracy - floating point and zero don't get along too well
            if (secondPath.getSpeeds()[i] == 0)
            {
                assert(std::abs(reachableSpeed) < NEGLIGIBLE_ERROR);
                // This won't influence the factor calculation - skip it so we don't divide by zero below
                continue;
            }

            if (std::signbit(reachableSpeed) != std::signbit(secondPath.getSpeeds()[i]))
            {
                assert(std::abs(reachableSpeed) < NEGLIGIBLE_ERROR);
                reachableSpeed = 0;
            }

            secondFactor = std::min(secondFactor, reachableSpeed / secondPath.getSpeeds()[i]);
        }
    }

    const VectorN finalSpeedJumps = firstJunctionSpeeds - secondPath.getSpeeds() * secondFactor;

    for (int i = 0; i < NUM_AXES; i++)
    {
        assert(std::abs(finalSpeedJumps[i]) - maxSpeedJumps[i] < NEGLIGIBLE_ERROR);
    }

    return secondFactor * secondPath.getFullSpeed();
}

double PathOptimizer::calculateSafeSpeed(const Path& path)
{
    double safeTime = 0;

    if (path.getDistance() == 0)
    {
        return 0;
    }

    for (int i = 0; i < NUM_AXES; i++)
    {
        const double safeAxisTime = std::abs(path.getWorldMove()[i]) / (maxSpeedJumps[i] / 2);
        assert(safeAxisTime >= 0);
        safeTime = std::max(safeTime, safeAxisTime);
    }

    const double safeSpeed = std::min(path.getDistance() / safeTime, path.getFullSpeed());
    assert(!std::isnan(safeSpeed));

    return safeSpeed;
}

void PathOptimizer::setMaxSpeedJumps(const VectorN& maxSpeedJumps)
{
    this->maxSpeedJumps = maxSpeedJumps;
}
