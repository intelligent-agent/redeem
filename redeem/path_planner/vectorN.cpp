// vectorN.cpp

#include "vectorN.h"
#include <math.h>

VectorN::VectorN()
{
  zero();
}

VectorN::VectorN(const VectorN &v)
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
VectorN& VectorN::operator+=(const VectorN &v)
{
  for (int i = 0; i < NUM_AXES; i++)
  {
    values[i] += v.values[i];
  }
  return *this;
}

VectorN& VectorN::operator-=(const VectorN &v)
{
  for (int i = 0; i < NUM_AXES; i++)
  {
    values[i] -= v.values[i];
  }
  return *this;
}

VectorN& VectorN::operator*=(FLOAT_T v)
{
  for (FLOAT_T& val : values)
  {
    val *= v;
  }
  return *this;
}

VectorN& VectorN::operator/=(FLOAT_T v)
{
  for (FLOAT_T& val : values)
  {
    val /= v;
  }
  return *this;
}

VectorN& VectorN::operator=(const VectorN &v)
{
  for (int i = 0; i < NUM_AXES; i++)
  {
    values[i] = v.values[i];
  }
  return *this;
}

VectorN& VectorN::norm()
{
  FLOAT_T mag = vabs(*this);
  if (mag > 0.0) {
    *this /= mag;
  }
  return *this;
}

FLOAT_T& VectorN::operator[](int i)
{
  return values[i];
}

const FLOAT_T& VectorN::operator[](int i) const
{
  return values[i];
}

// Helper functions for the VectorN class.

FLOAT_T vabs(const VectorN &v)
{
  FLOAT_T result = 0;
  for (double val : v.values)
  {
    result += val * val;
  }
  return sqrt(result);
}

VectorN unit(const VectorN &v)
{
  return v / vabs(v);
}

VectorN operator+(const VectorN &v)
{
  return v;
}

VectorN operator-(const VectorN &v)
{
  return v * -1.0;
}

VectorN operator+(const VectorN &v1, const VectorN &v2)
{
  VectorN result;

  for (int i = 0; i < NUM_AXES; i++)
  {
    result.values[i] = v1.values[i] + v2.values[i];
  }

  return result;
}

VectorN operator-(const VectorN &v1, const VectorN &v2)
{
  VectorN result;

  for (int i = 0; i < NUM_AXES; i++)
  {
    result.values[i] = v1.values[i] - v2.values[i];
  }

  return result;
}

bool equal(const VectorN &v1, const VectorN &v2, FLOAT_T tolerance)
{
  return vabs(v1 - v2) < tolerance;
}

VectorN operator*(const VectorN &v1, FLOAT_T v2)
{
  VectorN result(v1);

  result *= v2;

  return result;
}

VectorN operator*(FLOAT_T v1, const VectorN &v2)
{
  return v2 * v1;
}

VectorN operator/(const VectorN &v1, FLOAT_T v2)
{
  VectorN result(v1);

  result /= v2;

  return result;
}

FLOAT_T dot(const VectorN &v1, const VectorN &v2)
{
  FLOAT_T result = 0;

  for (int i = 0; i < NUM_AXES; i++)
  {
    result += v1.values[i] * v2.values[i];
  }

  return result;
}
