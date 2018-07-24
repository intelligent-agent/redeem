// vector3.cpp

#include "vector3.h"
#include "vectorN.h"
#include <assert.h>
#include <cmath>
#include <math.h>
#include <stdexcept>

// Constructors accept Cartesian coordinates or another vector.
Vector3::Vector3(double x, double y, double z)
    : x(x)
    , y(y)
    , z(z)
{
}
Vector3::Vector3(const Vector3& v)
    : x(v.x)
    , y(v.y)
    , z(v.z)
{
}
Vector3::~Vector3() {}

// some combined assignment, arithmetic operators.
Vector3& Vector3::operator+=(const Vector3& v)
{
    x += v.x;
    y += v.y;
    z += v.z;
    return *this;
}
Vector3& Vector3::operator-=(const Vector3& v)
{
    x -= v.x;
    y -= v.y;
    z -= v.z;
    return *this;
}
Vector3& Vector3::operator*=(double v)
{
    x *= v;
    y *= v;
    z *= v;
    return *this;
}
Vector3& Vector3::operator/=(double v)
{
    x /= v;
    y /= v;
    z /= v;
    return *this;
}
Vector3& Vector3::operator=(const Vector3& v)
{
    x = v.x;
    y = v.y;
    z = v.z;
    return *this;
}
Vector3& Vector3::norm()
{
    double mag = vabs(*this);
    if (mag > 0.0)
    {
        *this /= mag;
    }
    return *this;
}
double& Vector3::operator[](int i)
{
    switch (i)
    {
    case 0:
        return x;
    case 1:
        return y;
    case 2:
        return z;
    default:
        throw std::out_of_range("Vector3 index out of range");
    }
}
const double& Vector3::operator[](int i) const
{
    switch (i)
    {
    case 0:
        return x;
    case 1:
        return y;
    case 2:
        return z;
    default:
        throw std::out_of_range("Vector3 index out of range");
    }
}

/*
bool Vector3::operator==(const Vector3& o) const
{
  return x == o.x && y == o.y && z == o.z;
}
*/

IntVector3 Vector3::round() const
{
    return IntVector3(std::lround(x), std::lround(y), std::lround(z));
}

bool Vector3::hasNan() const
{
    return std::isnan(x) || std::isnan(y) || std::isnan(z);
}

// Helper functions for the Vector3 class.

double vabs(const Vector3& v)
{
    return sqrt(v.x * v.x + v.y * v.y + v.z * v.z);
}
Vector3 unit(const Vector3& v)
{
    return v / vabs(v);
}
Vector3 operator+(const Vector3& v)
{
    return Vector3(v.x, v.y, v.z);
}
Vector3 operator-(const Vector3& v)
{
    return Vector3(-v.x, -v.y, -v.z);
}
Vector3 operator+(const Vector3& v1, const Vector3& v2)
{
    return Vector3(v1.x + v2.x, v1.y + v2.y, v1.z + v2.z);
}
Vector3 operator-(const Vector3& v1, const Vector3& v2)
{
    return Vector3(v1.x - v2.x, v1.y - v2.y, v1.z - v2.z);
}
bool equal(const Vector3& v1, const Vector3& v2, double tolerance)
{
    return vabs(v1 - v2) < tolerance;
}
Vector3 operator*(const Vector3& v1, double v2)
{
    return Vector3(v1.x * v2, v1.y * v2, v1.z * v2);
}
Vector3 operator*(double v1, const Vector3& v2)
{
    return Vector3(v2.x * v1, v2.y * v1, v2.z * v1);
}
Vector3 operator/(const Vector3& v1, double v2)
{
    return Vector3(v1.x / v2, v1.y / v2, v1.z / v2);
}
double dot(const Vector3& v1, const Vector3& v2)
{
    return v1.x * v2.x + v1.y * v2.y + v1.z * v2.z;
}
Vector3 cross(const Vector3& v1, const Vector3& v2)
{
    Vector3 v3;
    v3.x = v1.y * v2.z - v2.y * v1.z;
    v3.y = v2.x * v1.z - v1.x * v2.z;
    v3.z = v1.x * v2.y - v2.x * v1.y;
    return v3;
}
Vector3 operator/(const Vector3& v1, const Vector3& v2)
{
    Vector3 v3;
    v3.x = v1.x / v2.x;
    v3.y = v1.y / v2.y;
    v3.z = v1.z / v2.z;
    return v3;
}
Vector3 operator*(const Vector3& v1, const Vector3& v2)
{
    Vector3 v3;
    v3.x = v1.x * v2.x;
    v3.y = v1.y * v2.y;
    v3.z = v1.z * v2.z;
    return v3;
}

IntVector3::IntVector3(int x, int y, int z)
    : x(x)
    , y(y)
    , z(z)
{
}

IntVector3::IntVector3(const IntVector3& o)
    : x(o.x)
    , y(o.y)
    , z(o.z)
{
}

IntVector3::~IntVector3()
{
}

IntVector3& IntVector3::operator=(const IntVector3& v)
{
    x = v.x;
    y = v.y;
    z = v.z;

    return *this;
}

IntVector3& IntVector3::operator+=(const IntVector3& v)
{
    x += v.x;
    y += v.y;
    z += v.z;

    return *this;
}

IntVector3& IntVector3::operator-=(const IntVector3& v)
{
    x -= v.x;
    y -= v.y;
    z -= v.z;

    return *this;
}

int& IntVector3::operator[](int i)
{
    switch (i)
    {
    case 0:
        return x;
    case 1:
        return y;
    case 2:
        return z;
    default:
        throw std::out_of_range("IntVector3 index out of range");
    }
}

const int& IntVector3::operator[](int i) const
{
    switch (i)
    {
    case 0:
        return x;
    case 1:
        return y;
    case 2:
        return z;
    default:
        throw std::out_of_range("IntVector3 index out of range");
    }
}

bool IntVector3::operator==(const IntVector3& o) const
{
    return x == o.x && y == o.y && z == o.z;
}

Vector3 IntVector3::toVector3() const
{
    return Vector3(x, y, z);
}