// vector8.h

#ifndef VECTOR8_H
#define VECTOR8_H

#include "config.h"

struct Vector3;
struct IntVectorN;
struct IntVector3;

struct VectorN {
  /// The Cartesian coordinates are accessible.
  double values[NUM_AXES];

  /// Copy constructor.
  VectorN(const VectorN &v);
  virtual ~VectorN();

  /// Default constructor.
  VectorN();

  /// Zeroes the values.
  void zero();

  // arithmetic operators follow; more are defined as helper functions, later.
  // We rely upon implicit conversions to get double and int operators.
  // Assignment operator
  VectorN& operator=(const VectorN &v);
  /// Add v to this vector.
  VectorN& operator+=(const VectorN &v);
  /// Subtract v from this vector.
  VectorN& operator-=(const VectorN &v);
  /// Scale by v (real number).
  VectorN& operator*=(double v);
  /// Scale by 1/v.
  VectorN& operator/=(double v);
  /// Normalize the vector (so that it is a unit vector.
  VectorN& norm();
  /// Get a specific axis of the vector
  double& operator[](int i);
  /// Same thing, but const
  const double& operator[](int i) const;
  /// Truncate to a Vector3
  Vector3 toVector3() const;
  /// Round to IntVectorN
  IntVectorN round() const;
};

// Helper functions.
/// Returns the magnitude of the vector.
double vabs(const VectorN &v);
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
bool equal(const VectorN &v1, const VectorN &v2, double tolerance = 1.0e-12);
/// Binary * returns a (new) vector (v1 * v2).
VectorN operator*(const VectorN &v1, double v2);
/// Binary * returns a (new) vector (v1 * v2).
VectorN operator*(double v1, const VectorN &v2);
/// Binary / returns a (new) vector (v1 / v2).
VectorN operator/(const VectorN &v1, double v2);
/// Vector dot product returns a real number.
double dot(const VectorN &v1, const VectorN &v2);
/// Element-wise division
VectorN operator/(const VectorN& v1, const VectorN& v2);
/// Element-wise multiplication
VectorN operator*(const VectorN& v1, const VectorN& v2);

struct IntVectorN {
  int values[NUM_AXES];

  IntVectorN();

  void zero();

  IntVectorN& operator=(const IntVectorN &v);
  /// Add v to this vector.
  IntVectorN& operator+=(const IntVectorN &v);
  /// Subtract v from this vector.
  IntVectorN& operator-=(const IntVectorN &v);
  /// Scale by v (integer)
  IntVectorN& operator*=(int v);
  /// Get a specific axis of the vector
  int& operator[](int i);
  /// Same thing, but const
  const int& operator[](int i) const;
  /// Convert to floating point
  VectorN toVectorN() const;
  /// Truncate to IntVector3
  IntVector3 toIntVector3() const;
};

/// Binary + returns new vector (v1 + v2).
IntVectorN operator+(const IntVectorN &v1, const IntVectorN &v2);
/// Binary - returns new vector (v1 - v2).
IntVectorN operator-(const IntVectorN &v1, const IntVectorN &v2);
/// Binary == check equality
bool operator==(const IntVectorN &v1, const IntVectorN &v2);
/// Binaru != check inequality
bool operator!=(const IntVectorN &v1, const IntVectorN &v2);

#endif
