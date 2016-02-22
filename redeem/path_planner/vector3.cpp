// vector3.cpp

#include <math.h>
#include "vector3.h"


// Constructors accept Cartesian coordinates or another vector.
Vector3::Vector3( FLOAT_T x, FLOAT_T y, FLOAT_T z )
    : x(x), y(y), z(z) {}
Vector3::Vector3( const Vector3 &v )
    : x(v.x), y(v.y), z(v.z) {}
Vector3::~Vector3() {}

// some combined assignment, arithmetic operators.
Vector3& Vector3::operator+=( const Vector3 &v )
{
    x += v.x; y += v.y; z += v.z;
    return *this;
}
Vector3& Vector3::operator-=( const Vector3 &v )
{
    x -= v.x; y -= v.y; z -= v.z;
    return *this;
}
Vector3& Vector3::operator*=( FLOAT_T v )
{
    x *= v; y *= v; z *= v;
    return *this;
}
Vector3& Vector3::operator/=( FLOAT_T v )
{
    x /= v; y /= v; z /= v;
    return *this;
}
Vector3& Vector3::operator=( const Vector3 &v )
{
    x = v.x; y = v.y; z = v.z;
    return *this;
}
Vector3& Vector3::norm()
{
    FLOAT_T mag = vabs(*this);
    if ( mag > 0.0 ) {
	*this /= mag;
    }
    return *this;
}

// Helper functions for the Vector3 class.

FLOAT_T vabs( const Vector3 &v )
{
    return sqrt(v.x*v.x + v.y*v.y + v.z*v.z);
}
Vector3 unit( const Vector3 &v )
{
    return v/vabs(v);
}
Vector3 operator+( const Vector3 &v )
{
    return Vector3(v.x, v.y, v.z);
}
Vector3 operator-( const Vector3 &v )
{
    return Vector3(-v.x, -v.y, -v.z);
}
Vector3 operator+( const Vector3 &v1, const Vector3 &v2 )
{
    return Vector3(v1.x + v2.x, v1.y + v2.y, v1.z + v2.z);
}
Vector3 operator-( const Vector3 &v1, const Vector3 &v2 )
{
    return Vector3(v1.x - v2.x, v1.y - v2.y, v1.z - v2.z);
}
bool equal( const Vector3 &v1, const Vector3 &v2, FLOAT_T tolerance)
{
    return vabs(v1 - v2) < tolerance;
}
Vector3 operator*( const Vector3 &v1, FLOAT_T v2 )
{
    return Vector3(v1.x*v2, v1.y*v2, v1.z*v2);
}
Vector3 operator*( FLOAT_T v1, const Vector3 &v2 )
{
    return Vector3(v2.x*v1, v2.y*v1, v2.z*v1);
}
Vector3 operator/( const Vector3 &v1, FLOAT_T v2 )
{
    return Vector3(v1.x/v2, v1.y/v2, v1.z/v2);
}
FLOAT_T dot( const Vector3 &v1, const Vector3 &v2 )
{
    return v1.x*v2.x + v1.y*v2.y + v1.z*v2.z;
}
Vector3 cross( const Vector3 &v1, const Vector3 &v2 )
{
    Vector3 v3;
    v3.x = v1.y*v2.z - v2.y*v1.z;
    v3.y = v2.x*v1.z - v1.x*v2.z;
    v3.z = v1.x*v2.y - v2.x*v1.y;
    return v3;
}
