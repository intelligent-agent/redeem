#pragma once

#include "PathOptimizerInterface.h"

class PathOptimizer final : public PathOptimizerInterface
{
private:
    friend struct PathOptimizerTests;

    VectorN maxSpeedJumps;

    std::tuple<double, double> calculateJunctionSpeed(const Path& previousPath, const Path& newPath);
    double calculateReachableJunctionSpeed(const Path& firstPath, const double firstOverallSpeed, const Path& secondSpeeds);
    double calculateSafeSpeed(const Path& path);
    bool doesJunctionSpeedViolateMaxSpeedJumps(const VectorN& entrySpeeds, const VectorN& exitSpeeds);

public:
    int64_t beforePathRemoval(std::vector<Path>& queue, PathQueueIndex first, PathQueueIndex last) override;
    int64_t onPathAdded(std::vector<Path>& queue, PathQueueIndex first, PathQueueIndex last) override;
    void setMaxSpeedJumps(const VectorN& maxSpeedJumps);
};