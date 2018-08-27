#pragma once

#include "PathOptimizerInterface.h"

class PathOptimizer final : public PathOptimizerInterface
{
private:
    VectorN maxSpeedJumps;

    void calculateJunctionSpeed(Path& previousPath, Path& newPath);
    void calculateSafeSpeed(Path& path);

public:
    int64_t beforePathRemoval(std::vector<Path>& queue, size_t first, size_t last) override;
    int64_t onPathAdded(std::vector<Path>& queue, size_t first, size_t last) override;
    void setMaxSpeedJumps(const VectorN& maxSpeedJumps);
};