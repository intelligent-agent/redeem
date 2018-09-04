#define _SILENCE_TR1_NAMESPACE_DEPRECATION_WARNING

#include "gtest/gtest.h"

#include <numeric>

#include "PathOptimizer.h"
#include "TestUtils.h"
#include "vector3.h"
#include "vectorN.h"

struct PathOptimizerTests : ::testing::Test
{
    PathBuilder builder;
    PathOptimizer optimizer;
    std::vector<Path> paths;
    PathQueueIndex firstPath;
    PathQueueIndex lastPath;

    PathOptimizerTests()
        : builder(PathBuilder::CartesianBuilder())
        , optimizer()
        , paths(10)
        , firstPath(0, 10)
        , lastPath(0, 10)
    {
        paths.resize(10);
        optimizer.setMaxSpeedJumps(builder.maxSpeedJumps);
    }

    int64_t addPath(Path&& p)
    {
        paths[lastPath.value] = std::move(p);
        return optimizer.onPathAdded(paths, firstPath, lastPath++);
    }

    void run()
    {
        std::vector<Path> result;

        for (PathQueueIndex i = firstPath; i != lastPath; i++)
        {
            optimizer.beforePathRemoval(paths, i, lastPath - 1);
        }
    }

    int64_t popPath()
    {
        return optimizer.beforePathRemoval(paths, firstPath++, lastPath - 1);
    }

    std::tuple<double, double> calculateJunctionSpeed(Path& firstPath, Path& secondPath)
    {
        return optimizer.calculateJunctionSpeed(firstPath, secondPath);
    }
};

TEST_F(PathOptimizerTests, OneMoveAtHalfMaxSpeedJump)
{
    addPath(builder.makePath(0.1, 0, 0, 0.005));
    run();

    // This move should be full speed the whole time - maxSpeedJump[x] is 0.01 so we can just jump to full speed
    EXPECT_DOUBLE_EQ(paths[0].getStartSpeed(), 0.005);
    EXPECT_DOUBLE_EQ(paths[0].getEndSpeed(), 0.005);
}

TEST_F(PathOptimizerTests, OneMoveAtMaxSpeedJump)
{
    addPath(builder.makePath(0.1, 0, 0, 0.01));
    run();

    // This move can't jump to full speed - we only use half of maxSpeedJump when starting fresh or stopping completely.
    EXPECT_DOUBLE_EQ(paths[0].getStartSpeed(), 0.005);
    EXPECT_DOUBLE_EQ(paths[0].getEndSpeed(), 0.005);
}

TEST_F(PathOptimizerTests, OneMoveAtLessThanMaxSpeedJump)
{
    addPath(builder.makePath(0.1, 0, 0, 0.001));
    run();

    EXPECT_DOUBLE_EQ(paths[0].getStartSpeed(), 0.001);
    EXPECT_DOUBLE_EQ(paths[0].getEndSpeed(), 0.001);
}

TEST_F(PathOptimizerTests, TwoMovesSameDirection)
{
    addPath(builder.makePath(0.1, 0, 0, 0.02));
    addPath(builder.makePath(0.1, 0, 0, 0.02));
    run();

    EXPECT_DOUBLE_EQ(paths[0].getStartSpeed(), 0.005);
    EXPECT_DOUBLE_EQ(paths[0].getEndSpeed(), 0.02);
    EXPECT_DOUBLE_EQ(paths[1].getStartSpeed(), 0.02);
    EXPECT_DOUBLE_EQ(paths[1].getEndSpeed(), 0.005);
}

TEST_F(PathOptimizerTests, TwoMovesSameDirectionWithSecondOneSlowerThanJerk)
{
    addPath(builder.makePath(0.1, 0, 0, 0.02));
    addPath(builder.makePath(0.1, 0, 0, 0.002));
    run();

    EXPECT_DOUBLE_EQ(paths[0].getStartSpeed(), 0.005);
    EXPECT_DOUBLE_EQ(paths[0].getEndSpeed(), 0.012);
    EXPECT_DOUBLE_EQ(paths[1].getStartSpeed(), 0.002);
    EXPECT_DOUBLE_EQ(paths[1].getEndSpeed(), 0.002);
}

TEST_F(PathOptimizerTests, TwoMovesRightAngle)
{
    addPath(builder.makePath(0.1, 0, 0, 0.02));
    addPath(builder.makePath(0, 0.1, 0, 0.02));
    run();

    EXPECT_DOUBLE_EQ(paths[0].getStartSpeed(), 0.005); // We can only use half of maxSpeedJump because we don't know what X was doing before this move
    EXPECT_DOUBLE_EQ(paths[0].getEndSpeed(), 0.01); // We can use all of maxSpeedJump because we know the next move
    EXPECT_DOUBLE_EQ(paths[1].getStartSpeed(), 0.01); // Same again - Y is jumping from 0 to 0.01
    EXPECT_DOUBLE_EQ(paths[1].getEndSpeed(), 0.005); // back to half because Y is jumping from 0.005 to <unknown>
}

TEST_F(PathOptimizerTests, TwoMovesSlowingDown)
{
    addPath(builder.makePath(0.1, 0, 0, 0.03));
    addPath(builder.makePath(0.1, 0, 0, 0.02));
    run();

    EXPECT_DOUBLE_EQ(paths[0].getStartSpeed(), 0.005);
    EXPECT_DOUBLE_EQ(paths[0].getEndSpeed(), 0.03);
    EXPECT_DOUBLE_EQ(paths[1].getStartSpeed(), 0.02);
    EXPECT_DOUBLE_EQ(paths[1].getEndSpeed(), 0.005);
}

TEST_F(PathOptimizerTests, TwoMovesSpeedingUp)
{
    addPath(builder.makePath(0.1, 0, 0, 0.02));
    addPath(builder.makePath(0.1, 0, 0, 0.03));
    run();

    EXPECT_DOUBLE_EQ(paths[0].getStartSpeed(), 0.005);
    EXPECT_DOUBLE_EQ(paths[0].getEndSpeed(), 0.02);
    EXPECT_DOUBLE_EQ(paths[1].getStartSpeed(), 0.03);
    EXPECT_DOUBLE_EQ(paths[1].getEndSpeed(), 0.005);
}

TEST_F(PathOptimizerTests, TwoMoves45DegreeAngle)
{
    addPath(builder.makePath(0.1, 0, 0, 0.01));
    addPath(builder.makePath(0.1, 0.1, 0, 0.01));
    run();

    EXPECT_DOUBLE_EQ(paths[0].getStartSpeed(), 0.005);
    EXPECT_DOUBLE_EQ(paths[0].getEndSpeed(), 0.01);
    EXPECT_DOUBLE_EQ(paths[1].getStartSpeed(), 0.01);
    EXPECT_DOUBLE_EQ(paths[1].getEndSpeed(), vabs(VectorN(0.005, 0.005, 0)));
}

TEST_F(PathOptimizerTests, ThreeMovesThatFormTrapezoid)
{
    // per vf^2 = v0^2 + 2*a*d
    // if we start at 0.005m/s, accelerate at 0.1m/s^2, and travel 0.1m, we should reach 0.1415m/s

    addPath(builder.makePath(0.1, 0, 0, 1.0));
    addPath(builder.makePath(0.1, 0, 0, 1.0));
    addPath(builder.makePath(0.1, 0, 0, 1.0));
    run();

    // calculated in Maxima as sqrt(v0^2 + 2*a*d)
    EXPECT_DOUBLE_EQ(paths[0].getStartSpeed(), 0.005);
    EXPECT_DOUBLE_EQ(paths[0].getEndSpeed(), 0.1415097169808491);
    EXPECT_DOUBLE_EQ(paths[1].getStartSpeed(), 0.1515097169808491);
    EXPECT_DOUBLE_EQ(paths[1].getEndSpeed(), 0.1515097169808491);
    EXPECT_DOUBLE_EQ(paths[2].getStartSpeed(), 0.1415097169808491);
    EXPECT_DOUBLE_EQ(paths[2].getEndSpeed(), 0.005);
}

TEST_F(PathOptimizerTests, FiveMovesThatFormTrapezoid)
{
    addPath(builder.makePath(0.1, 0, 0, 1.0));
    addPath(builder.makePath(0.1, 0, 0, 1.0));
    addPath(builder.makePath(0.1, 0, 0, 1.0));
    addPath(builder.makePath(0.1, 0, 0, 1.0));
    addPath(builder.makePath(0.1, 0, 0, 1.0));
    run();

    EXPECT_DOUBLE_EQ(paths[0].getStartSpeed(), 0.005);
    EXPECT_DOUBLE_EQ(paths[0].getEndSpeed(), 0.1415097169808491);
    EXPECT_DOUBLE_EQ(paths[1].getStartSpeed(), 0.1515097169808491);
    EXPECT_DOUBLE_EQ(paths[1].getEndSpeed(), 0.20725634933486836);
    EXPECT_DOUBLE_EQ(paths[2].getStartSpeed(), 0.21725634933486837);
    EXPECT_DOUBLE_EQ(paths[2].getEndSpeed(), 0.21725634933486837);
    EXPECT_DOUBLE_EQ(paths[3].getStartSpeed(), 0.20725634933486836);
    EXPECT_DOUBLE_EQ(paths[3].getEndSpeed(), 0.1515097169808491);
    EXPECT_DOUBLE_EQ(paths[4].getStartSpeed(), 0.1415097169808491);
    EXPECT_DOUBLE_EQ(paths[4].getEndSpeed(), 0.005);
}

TEST_F(PathOptimizerTests, SevenMovesThatFormTrapezoid)
{
    addPath(builder.makePath(0.1, 0, 0, 1.0));
    addPath(builder.makePath(0.1, 0, 0, 1.0));
    addPath(builder.makePath(0.1, 0, 0, 1.0));
    addPath(builder.makePath(0.1, 0, 0, 1.0));
    addPath(builder.makePath(0.1, 0, 0, 1.0));
    addPath(builder.makePath(0.1, 0, 0, 1.0));
    addPath(builder.makePath(0.1, 0, 0, 1.0));
    run();

    EXPECT_DOUBLE_EQ(paths[0].getStartSpeed(), 0.005);
    EXPECT_DOUBLE_EQ(paths[0].getEndSpeed(), 0.1415097169808491);
    EXPECT_DOUBLE_EQ(paths[1].getStartSpeed(), 0.1515097169808491);
    EXPECT_DOUBLE_EQ(paths[1].getEndSpeed(), 0.20725634933486836);
    EXPECT_DOUBLE_EQ(paths[2].getStartSpeed(), 0.21725634933486836);
    EXPECT_DOUBLE_EQ(paths[2].getEndSpeed(), 0.25923024770715775);
    EXPECT_DOUBLE_EQ(paths[3].getStartSpeed(), 0.26923024770715775);
    EXPECT_DOUBLE_EQ(paths[3].getEndSpeed(), 0.26923024770715775);
    EXPECT_DOUBLE_EQ(paths[4].getStartSpeed(), 0.25923024770715775);
    EXPECT_DOUBLE_EQ(paths[4].getEndSpeed(), 0.21725634933486836);
    EXPECT_DOUBLE_EQ(paths[5].getStartSpeed(), 0.20725634933486836);
    EXPECT_DOUBLE_EQ(paths[5].getEndSpeed(), 0.1515097169808491);
    EXPECT_DOUBLE_EQ(paths[6].getStartSpeed(), 0.1415097169808491);
    EXPECT_DOUBLE_EQ(paths[6].getEndSpeed(), 0.005);
}

TEST_F(PathOptimizerTests, AddingAPathReturnsEstimatedTime)
{
    EXPECT_EQ(addPath(builder.makePath(0.1, 0, 0, 0.005)), 4000000000ll);
}

TEST_F(PathOptimizerTests, RemovingAPathReturnsEstimatedTime)
{
    addPath(builder.makePath(0.1, 0, 0, 0.005));
    EXPECT_EQ(popPath(), -20ll * F_CPU);
}

/*
This test is out for now - it reflects a more complicated time calculation that we can't currently do.
TODO make move time estimations more accurate :)

TEST_F(PathOptimizerTests, AddingASecondPathReturnsTimeChange)
{
    // this path will start and end at 0.005 but cruise at 0.105
    // accelerating will take 1 second, during which we'll travel 0.055m
    // that means another second to decelerate at the end and another second to cruise the remaining 0.105
    EXPECT_EQ(addPath(builder.makePath(0.215, 0, 0, 0.105)), 3ll * F_CPU);

    // adding another one in the same direction means we now travel a total of 0.320.
    // 0.11 of that will be used in accel/decel, leaving 0.210 or 2 seconds of cruise
    // since the total queue time is changing from 3 seconds to 4 seconds, we should only see the delta returned
    EXPECT_EQ(addPath(builder.makePath(0.105, 0, 0, 0.105)), 1ll * F_CPU);
}
*/

// Instead of that, let's test the simple estimation we have now
TEST_F(PathOptimizerTests, AddingASecondPathReturnsTimeChange)
{
    EXPECT_EQ(addPath(builder.makePath(0.2, 0, 0, 0.1)), 2ll * F_CPU);
    EXPECT_EQ(addPath(builder.makePath(0.2, 0, 0, 0.1)), 2ll * F_CPU);
}

TEST_F(PathOptimizerTests, CorrectlyWrapsAroundAtQueueEnd)
{
    firstPath = lastPath = PathQueueIndex(paths.size() - 1, paths.size());

    addPath(builder.makePath(0.2, 0, 0, 0.2));
    addPath(builder.makePath(0.2, 0, 0, 0.2));

    ASSERT_EQ(lastPath.value, 1);

    EXPECT_DOUBLE_EQ(paths[firstPath.value].getMaxEndSpeed(), 0.2);
    EXPECT_DOUBLE_EQ(paths[(firstPath + 1).value].getMaxStartSpeed(), 0.2);
}

TEST_F(PathOptimizerTests, FullSpeedJunction)
{
    Path firstPath = builder.makePath(0.2, 0, 0, 0.2);
    Path secondPath = builder.makePath(0.2, 0, 0, 0.2);

    auto [firstSpeed, secondSpeed] = calculateJunctionSpeed(firstPath, secondPath);

    EXPECT_DOUBLE_EQ(firstSpeed, 0.2);
    EXPECT_DOUBLE_EQ(secondSpeed, 0.2);
}

TEST_F(PathOptimizerTests, FullSpeedJunctionNegative)
{
    Path firstPath = builder.makePath(-0.2, 0, 0, 0.2);
    Path secondPath = builder.makePath(-0.2, 0, 0, 0.2);

    auto [firstSpeed, secondSpeed] = calculateJunctionSpeed(firstPath, secondPath);

    EXPECT_DOUBLE_EQ(firstSpeed, 0.2);
    EXPECT_DOUBLE_EQ(secondSpeed, 0.2);
}

TEST_F(PathOptimizerTests, SafeSpeedJunction)
{
    Path firstPath = builder.makePath(0.2, 0, 0, 0.2);
    Path secondPath = builder.makePath(-0.2, 0, 0, 0.2);

    auto [firstSpeed, secondSpeed] = calculateJunctionSpeed(firstPath, secondPath);

    EXPECT_DOUBLE_EQ(firstSpeed, 0.005);
    EXPECT_DOUBLE_EQ(secondSpeed, 0.005);
}

TEST_F(PathOptimizerTests, SafeSpeedJunctionNegative)
{
    Path firstPath = builder.makePath(-0.2, 0, 0, 0.2);
    Path secondPath = builder.makePath(0.2, 0, 0, 0.2);

    auto [firstSpeed, secondSpeed] = calculateJunctionSpeed(firstPath, secondPath);

    EXPECT_DOUBLE_EQ(firstSpeed, 0.005);
    EXPECT_DOUBLE_EQ(secondSpeed, 0.005);
}

TEST_F(PathOptimizerTests, SpeedJumpJunction)
{
    Path firstPath = builder.makePath(0.2, 0, 0, 0.2);
    Path secondPath = builder.makePath(0, 0.2, 0, 0.2);

    auto [firstSpeed, secondSpeed] = calculateJunctionSpeed(firstPath, secondPath);

    EXPECT_DOUBLE_EQ(firstSpeed, 0.01);
    EXPECT_DOUBLE_EQ(secondSpeed, 0.01);
}

TEST_F(PathOptimizerTests, SpeedJumpJunctionNegative)
{
    Path firstPath = builder.makePath(-0.2, 0, 0, 0.2);
    Path secondPath = builder.makePath(0, -0.2, 0, 0.2);

    auto [firstSpeed, secondSpeed] = calculateJunctionSpeed(firstPath, secondPath);

    EXPECT_DOUBLE_EQ(firstSpeed, 0.01);
    EXPECT_DOUBLE_EQ(secondSpeed, 0.01);
}

TEST_F(PathOptimizerTests, 45DegreeAngle)
{
    Path firstPath = builder.makePath(0.1, 0, 0, 0.2);
    Path secondPath = builder.makePath(0.1, 0.1, 0, 0.2);

    auto [firstSpeed, secondSpeed] = calculateJunctionSpeed(firstPath, secondPath);

    EXPECT_DOUBLE_EQ(firstSpeed, 0.014142135623730951);
    EXPECT_DOUBLE_EQ(secondSpeed, 0.014142135623730951);
}

TEST_F(PathOptimizerTests, 135DegreeAngle)
{
    Path firstPath = builder.makePath(0.1, 0, 0, 0.2);
    Path secondPath = builder.makePath(-0.1, 0.1, 0, 0.2);

    auto [firstSpeed, secondSpeed] = calculateJunctionSpeed(firstPath, secondPath);

    EXPECT_DOUBLE_EQ(firstSpeed, 0.005);
    EXPECT_DOUBLE_EQ(secondSpeed, 0.0070710678118654762);
}
