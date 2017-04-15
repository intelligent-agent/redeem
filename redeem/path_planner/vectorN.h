// vector8.h

#ifndef VECTOR8_H
#define VECTOR8_H

#include "config.h"

class Vector3;
class IntVectorN;
class IntVector3;

struct VectorN {
  /// The Cartesian coordinates are accessible.
  FLOAT_T values[NUM_AXES];

  /// Copy constructor.
  VectorN(const VectorN &v);
  virtual ~VectorN();

  /// Default constructor.
  VectorN();

  /// Zeroes the values.
  void zero();

  // arithmetic operators follow; more are defined as helper functions, later.
  // We rely upon implicit conversions to get FLOAT_T and int operators.
  // Assignment operator
  VectorN& operator=(const VectorN &v);
  /// Add v to this vector.
  VectorN& operator+=(const VectorN &v);
  /// Subtract v from this vector.
  VectorN& operator-=(const VectorN &v);
  /// Scale by v (real number).
  VectorN& operator*=(FLOAT_T v);
  /// Scale by 1/v.
  VectorN& operator/=(FLOAT_T v);
  /// Normalize the vector (so that it is a unit vector.
  VectorN& norm();
  /// Get a specific axis of the vector
  FLOAT_T& operator[](int i);
  /// Same thing, but const
  const FLOAT_T& operator[](int i) const;
  /// Truncate to a Vector3
  Vector3 toVector3() const;
  /// Round to IntVectorN
  IntVectorN round() const;
};

// Helper functions.
/// Returns the magnitude of the vector.
FLOAT_T vabs(const VectorN &v);
/// Returns a (new) unit vector with the same direction as v.
VectorN unit(const VectorN &v);
/// Unary +
VectorN operator+(const VectorN &v);
/// Unary -
VectorN operator-(const VectorN &v);
/// Binary + returns new vector (v1 + v2).
VectorN operator+(const VectorN &v1, const VectorN &v2);
/// Binary - returns new vector (v1 - v2).
VectorN operator-(const VectorN &v1, const VectorN &v2);
/// Returns True if v1 and v2 are within tolerance of each other.
bool equal(const VectorN &v1, const VectorN &v2, FLOAT_T tolerance = 1.0e-12);
/// Binary * returns a (new) vector (v1 * v2).
VectorN operator*(const VectorN &v1, FLOAT_T v2);
/// Binary * returns a (new) vector (v1 * v2).
VectorN operator*(FLOAT_T v1, const VectorN &v2);
/// Binary / returns a (new) vector (v1 / v2).
VectorN operator/(const VectorN &v1, FLOAT_T v2);
/// Vector dot product returns a real number.
FLOAT_T dot(const VectorN &v1, const VectorN &v2);
/// Element-wise division
VectorN operator/(const VectorN& v1, const VectorN& v2);
/// Element-wise multiplication
VectorN operator*(const VectorN& v1, const VectorN& v2);

struct IntVectorN {
  long long values[NUM_AXES];

  IntVectorN();

  void zero();

  IntVectorN& operator=(const IntVectorN &v);
  /// Add v to this vector.
  IntVectorN& operator+=(const IntVectorN &v);
  /// Subtract v from this vector.
  IntVectorN& operator-=(const IntVectorN &v);
  /// Scale by v (integer)
  IntVectorN& operator*=(long long v);
  /// Get a specific axis of the vector
  long long& operator[](int i);
  /// Same thing, but const
  const long long& operator[](int i) const;
  /// Convert to floating point
  VectorN toVectorN() const;
  /// Truncate to IntVector3
  IntVector3 toIntVector3() const;
};

/// Binary + returns new vector (v1 + v2).
IntVectorN operator+(const IntVectorN &v1, const IntVectorN &v2);
/// Binary - returns new vector (v1 - v2).
IntVectorN operator-(const IntVectorN &v1, const IntVectorN &v2);



#endif
