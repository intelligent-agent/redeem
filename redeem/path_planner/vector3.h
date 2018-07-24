// vector3.h

#ifndef VECTOR3_H
#define VECTOR3_H

#include "config.h"

struct IntVector3;

struct Vector3 {
    /// The Cartesian coordinates are accessible.
    double x;
    double y;
    double z;
    /// Constructor accept Cartesian coordinates.
    Vector3( double x=0.0, double y=0.0, double z=0.0 );
    /// Copy constructor.
    Vector3(const Vector3&);
    ~Vector3();

    // arithmetic operators follow; more are defined as helper functions, later.
    // We rely upon implicit conversions to get double and int operators.
    // Assignment operator
    Vector3& operator=( const Vector3 &v );
    /// Add v to this vector.
    Vector3& operator+=( const Vector3 &v );
    /// Subtract v from this vector.
    Vector3& operator-=( const Vector3 &v );
    /// Scale by v (real number).
    Vector3& operator*=( double v );
    /// Scale by 1/v.
    Vector3& operator/=( double v );
    /// Normalize the vector (so that it is a unit vector.
    Vector3& norm();
    /// Get a specific axis of the vector
    double& operator[](int i);
    /// Same thing, but const
    const double& operator[](int i) const;

    IntVector3 round() const;

    bool hasNan() const;

    //bool operator==(const Vector3& o) const;
    //bool operator!=(const Vector3& o) const { return !(*this == o); };
};

// Helper functions.
/// Returns the magnitude of the vector.
double vabs( const Vector3 &v );
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
bool equal( const Vector3 &v1, const Vector3 &v2, double tolerance=1.0e-12);
/// Binary * returns a (new) vector (v1 * v2).
Vector3 operator*( const Vector3 &v1, double v2 );
/// Binary * returns a (new) vector (v1 * v2).
Vector3 operator*(double v1, const Vector3 &v2 );
/// Binary / returns a (new) vector (v1 / v2).
Vector3 operator/( const Vector3 &v1, double v2 );
/// Vector dot product returns a real number.
double dot( const Vector3 &v1, const Vector3 &v2 );
/// Vector cross product returns a (new) vector value.
Vector3 cross( const Vector3 &v1, const Vector3 &v2 );
/// Element-wise division
Vector3 operator/(const Vector3 &v1, const Vector3 &v2);
/// Element-wise multiplication
Vector3 operator*(const Vector3 &v1, const Vector3 &v2);

struct IntVector3
{
  int x;
  int y;
  int z;

  /// Constructor accept Cartesian coordinates.
  IntVector3(int x = 0.0, int y = 0.0, int z = 0.0);
  /// Copy constructor.
  IntVector3(const IntVector3&);
  ~IntVector3();

  // arithmetic operators follow; more are defined as helper functions, later.
  // We rely upon implicit conversions to get double and int operators.
  // Assignment operator
  IntVector3& operator=(const IntVector3 &v);
  /// Add v to this vector.
  IntVector3& operator+=(const IntVector3 &v);
  /// Subtract v from this vector.
  IntVector3& operator-=(const IntVector3 &v);
  /// Get a specific axis of the vector
  int& operator[](int i);
  /// Same thing, but const
  const int& operator[](int i) const;

  bool operator==(const IntVector3& o) const;
  bool operator!=(const IntVector3& o) const { return !(*this == o); };

  Vector3 toVector3() const;
};

// Helper functions.
/// Returns the magnitude of the vector.
double vabs(const IntVector3 &v);
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
