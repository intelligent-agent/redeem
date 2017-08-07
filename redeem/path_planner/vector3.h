// vector3.h

#ifndef VECTOR3_H
#define VECTOR3_H

#include "config.h"

class IntVector3;

struct Vector3 {
    /// The Cartesian coordinates are accessible.
    FLOAT_T x;
    FLOAT_T y;
    FLOAT_T z;
    /// Constructor accept Cartesian coordinates.
    Vector3( FLOAT_T x=0.0, FLOAT_T y=0.0, FLOAT_T z=0.0 );
    /// Copy constructor.
    Vector3(const Vector3&);
    ~Vector3();

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
    /// Get a specific axis of the vector
    FLOAT_T& operator[](int i);
    /// Same thing, but const
    const FLOAT_T& operator[](int i) const;

    IntVector3 round() const;

    //bool operator==(const Vector3& o) const;
    //bool operator!=(const Vector3& o) const { return !(*this == o); };
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
Vector3 operator*(FLOAT_T v1, const Vector3 &v2 );
/// Binary / returns a (new) vector (v1 / v2).
Vector3 operator/( const Vector3 &v1, FLOAT_T v2 );
/// Vector dot product returns a real number.
FLOAT_T dot( const Vector3 &v1, const Vector3 &v2 );
/// Vector cross product returns a (new) vector value.
Vector3 cross( const Vector3 &v1, const Vector3 &v2 );
/// Element-wise division
Vector3 operator/(const Vector3 &v1, const Vector3 &v2);
/// Element-wise multiplication
Vector3 operator*(const Vector3 &v1, const Vector3 &v2);

struct IntVector3
{
  // TODO I suspect it's safe to make these ints.
  long long x;
  long long y;
  long long z;

  /// Constructor accept Cartesian coordinates.
  IntVector3(long long x = 0.0, long long y = 0.0, long long z = 0.0);
  /// Copy constructor.
  IntVector3(const IntVector3&);
  ~IntVector3();

  // arithmetic operators follow; more are defined as helper functions, later.
  // We rely upon implicit conversions to get FLOAT_T and int operators.
  // Assignment operator
  IntVector3& operator=(const IntVector3 &v);
  /// Add v to this vector.
  IntVector3& operator+=(const IntVector3 &v);
  /// Subtract v from this vector.
  IntVector3& operator-=(const IntVector3 &v);
  /// Get a specific axis of the vector
  long long& operator[](int i);
  /// Same thing, but const
  const long long& operator[](int i) const;

  bool operator==(const IntVector3& o) const;
  bool operator!=(const IntVector3& o) const { return !(*this == o); };

  Vector3 toVector3() const;
};

// Helper functions.
/// Returns the magnitude of the vector.
FLOAT_T vabs(const IntVector3 &v);
/// Returns a (new) unit vector with the same direction as v.
IntVector3 unit(const IntVector3 &v);
/// Unary +
IntVector3 operator+(const IntVector3 &v);
/// Unary -
IntVector3 operator-(const IntVector3 &v);
/// Binary + returns new vector (v1 + v2).
IntVector3 operator+(const IntVector3 &v1, const IntVector3 &v2);
/// Binary - returns new vector (v1 - v2).
IntVector3 operator-(const IntVector3 &v1, const IntVector3 &v2);

#endif
