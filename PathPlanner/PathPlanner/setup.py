#!/usr/bin/env python

from distutils.core import setup, Extension

module1 = Extension('_PathPlannerNative', sources = ['PathPlannerNative.i', 'PathPlanner.cpp','PruTimer.cpp','prussdrv.c','Logger.cpp'],  swig_opts=['-c++','-builtin'], extra_compile_args = ['-std=c++0x','-g','-O0','-fpermissive','-UNDEBUG'])

setup(name='PathPlannerNative',
      version='1.0',
      description='PathPlanner for 3D printer',
      author='Mathieu Monney',
      author_email='zittix@xwaves.net',
      url='http://www.xwaves.net',
      ext_modules = [module1],
     )
