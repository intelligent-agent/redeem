// vector3.h

#ifndef VECTOR3_H
#define VECTOR3_H

#include "config.h"

class Vector3 {
public:
    /// The Cartesian coordinates are accessible.
    FLOAT_T x;
    FLOAT_T y;
    FLOAT_T z;
    /// Constructor accept Cartesian coordinates.
    Vector3( FLOAT_T x=0.0, FLOAT_T y=0.0, FLOAT_T z=0.0 );
    /// Copy constructor.
    Vector3( const Vector3 &v );
    virtual ~Vector3();

    // arithmetic operators follow; more are defined as helper functions, later.
    // We rely upon implicit conversions to get FLOAT_T and int operators.
    // Assignment operator
    Vector3& operator=( const Vector3 &v );
    /// Add v to this vector.
    Vector3& operator+=( const Vector3 &v );
    /// Subtract v from this vector.
    Vector3& operator-=( const Vector3 &v );
    /// Scale by v (real number).
    Vector3& operator*=( FLOAT_T v );
    /// Scale by 1/v.
    Vector3& operator/=( FLOAT_T v );
    /// Normalize the vector (so that it is a unit vector.
    Vector3& norm();
};

// Helper functions.
/// Returns the magnitude of the vector.
FLOAT_T vabs( const Vector3 &v );
/// Returns a (new) unit vector with the same direction as v.
Vector3 unit( const Vector3 &v );
/// Unary +
Vector3 operator+( const Vector3 &v );
/// Unary -
Vector3 operator-( const Vector3 &v );
/// Binary + returns new vector (v1 + v2).
Vector3 operator+( const Vector3 &v1, const Vector3 &v2 );
/// Binary - returns new vector (v1 - v2).
Vector3 operator-( const Vector3 &v1, const Vector3 &v2 );
/// Returns True if v1 and v2 are within tolerance of each other.
bool equal( const Vector3 &v1, const Vector3 &v2, FLOAT_T tolerance=1.0e-12);
/// Binary * returns a (new) vector (v1 * v2).
Vector3 operator*( const Vector3 &v1, FLOAT_T v2 );
/// Binary * returns a (new) vector (v1 * v2).
Vector3 operator*( FLOAT_T v1, const Vector3 &v2 );
/// Binary / returns a (new) vector (v1 / v2).
Vector3 operator/( const Vector3 &v1, FLOAT_T v2 );
/// Vector dot product returns a real number.
FLOAT_T dot( const Vector3 &v1, const Vector3 &v2 );
/// Vector cross product returns a (new) vector value.
Vector3 cross( const Vector3 &v1, const Vector3 &v2 );

#endif
