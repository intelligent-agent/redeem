// vectorN.cpp

#include "vectorN.h"
#include "vector3.h"
#include <cmath>
#include <math.h>

VectorN::VectorN()
{
    zero();
}

VectorN::VectorN(const VectorN& v)
{
    for (int i = 0; i < NUM_AXES; i++)
    {
        values[i] = v.values[i];
    }
}

VectorN::~VectorN() {}

void VectorN::zero()
{
    for (int i = 0; i < NUM_AXES; i++)
    {
        values[i] = 0;
    }
}

// some combined assignment, arithmetic operators.
VectorN& VectorN::operator+=(const VectorN& v)
{
    for (int i = 0; i < NUM_AXES; i++)
    {
        values[i] += v.values[i];
    }
    return *this;
}

VectorN& VectorN::operator-=(const VectorN& v)
{
    for (int i = 0; i < NUM_AXES; i++)
    {
        values[i] -= v.values[i];
    }
    return *this;
}

VectorN& VectorN::operator*=(double v)
{
    for (double& val : values)
    {
        val *= v;
    }
    return *this;
}

VectorN& VectorN::operator/=(double v)
{
    for (double& val : values)
    {
        val /= v;
    }
    return *this;
}

VectorN& VectorN::operator=(const VectorN& v)
{
    for (int i = 0; i < NUM_AXES; i++)
    {
        values[i] = v.values[i];
    }
    return *this;
}

VectorN& VectorN::norm()
{
    double mag = vabs(*this);
    if (mag > 0.0)
    {
        *this /= mag;
    }
    return *this;
}

double& VectorN::operator[](int i)
{
    return values[i];
}

const double& VectorN::operator[](int i) const
{
    return values[i];
}

Vector3 VectorN::toVector3() const
{
    return Vector3(values[0], values[1], values[2]);
}

IntVectorN VectorN::round() const
{
    IntVectorN result;
    for (int i = 0; i < NUM_AXES; i++)
    {
        result[i] = std::lround(values[i]);
    }

    return result;
}

// Helper functions for the VectorN class.

double vabs(const VectorN& v)
{
    double result = 0;
    for (double val : v.values)
    {
        result += val * val;
    }
    return sqrt(result);
}

VectorN unit(const VectorN& v)
{
    return v / vabs(v);
}

VectorN operator+(const VectorN& v)
{
    return v;
}

VectorN operator-(const VectorN& v)
{
    return v * -1.0;
}

VectorN operator+(const VectorN& v1, const VectorN& v2)
{
    VectorN result;

    for (int i = 0; i < NUM_AXES; i++)
    {
        result.values[i] = v1.values[i] + v2.values[i];
    }

    return result;
}

VectorN operator-(const VectorN& v1, const VectorN& v2)
{
    VectorN result;

    for (int i = 0; i < NUM_AXES; i++)
    {
        result.values[i] = v1.values[i] - v2.values[i];
    }

    return result;
}

bool equal(const VectorN& v1, const VectorN& v2, double tolerance)
{
    return vabs(v1 - v2) < tolerance;
}

VectorN operator*(const VectorN& v1, double v2)
{
    VectorN result(v1);

    result *= v2;

    return result;
}

VectorN operator*(double v1, const VectorN& v2)
{
    return v2 * v1;
}

VectorN operator/(const VectorN& v1, double v2)
{
    VectorN result(v1);

    result /= v2;

    return result;
}

double dot(const VectorN& v1, const VectorN& v2)
{
    double result = 0;

    for (int i = 0; i < NUM_AXES; i++)
    {
        result += v1.values[i] * v2.values[i];
    }

    return result;
}

VectorN operator/(const VectorN& v1, const VectorN& v2)
{
    VectorN v3;
    for (int i = 0; i < NUM_AXES; i++)
    {
        v3[i] = v1[i] / v2[i];
    }
    return v3;
}

VectorN operator*(const VectorN& v1, const VectorN& v2)
{
    VectorN v3;
    for (int i = 0; i < NUM_AXES; i++)
    {
        v3[i] = v1[i] * v2[i];
    }
    return v3;
}

IntVectorN::IntVectorN()
{
    zero();
}

void IntVectorN::zero()
{
    for (int i = 0; i < NUM_AXES; i++)
    {
        values[i] = 0;
    }
}

IntVectorN& IntVectorN::operator=(const IntVectorN& v)
{
    for (int i = 0; i < NUM_AXES; i++)
    {
        values[i] = v[i];
    }

    return *this;
}

IntVectorN& IntVectorN::operator+=(const IntVectorN& v)
{
    for (int i = 0; i < NUM_AXES; i++)
    {
        values[i] += v[i];
    }

    return *this;
}

IntVectorN& IntVectorN::operator-=(const IntVectorN& v)
{
    for (int i = 0; i < NUM_AXES; i++)
    {
        values[i] -= v[i];
    }

    return *this;
}

IntVectorN& IntVectorN::operator*=(int v)
{
    for (int i = 0; i < NUM_AXES; i++)
    {
        values[i] *= v;
    }

    return *this;
}

int& IntVectorN::operator[](int i)
{
    return values[i];
}

const int& IntVectorN::operator[](int i) const
{
    return values[i];
}

VectorN IntVectorN::toVectorN() const
{
    VectorN result;
    for (int i = 0; i < NUM_AXES; i++)
    {
        result[i] = values[i];
    }

    return result;
}

IntVector3 IntVectorN::toIntVector3() const
{
    return IntVector3(values[0], values[1], values[2]);
}

IntVectorN operator+(const IntVectorN& v1, const IntVectorN& v2)
{
    IntVectorN result;

    for (int i = 0; i < NUM_AXES; i++)
    {
        result[i] = v1[i] + v2[i];
    }

    return result;
}

IntVectorN operator-(const IntVectorN& v1, const IntVectorN& v2)
{
    IntVectorN result;

    for (int i = 0; i < NUM_AXES; i++)
    {
        result[i] = v1[i] - v2[i];
    }

    return result;
}

bool operator==(const IntVectorN& v1, const IntVectorN& v2)
{
    for (int i = 0; i < NUM_AXES; i++)
    {
        if (v1[i] != v2[i])
        {
            return false;
        }
    }

    return true;
}

bool operator!=(const IntVectorN& v1, const IntVectorN& v2)
{
    return !(v1 == v2);
}