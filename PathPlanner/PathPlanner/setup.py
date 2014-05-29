#!/usr/bin/env python

from distutils.core import setup, Extension

module1 = Extension('_pathplanner', sources = ['PathPlanner.i', 'PathPlanner.cpp','PruTimer.cpp','prussdrv.c'],  swig_opts=['-c++','-builtin'], extra_compile_args = ['-std=c++0x','-g','-O0','-fpermissive'])

setup(name='PathPlanner',
      version='1.0',
      description='PathPlanner for 3D printer',
      author='Mathieu Monney',
      author_email='zittix@xwaves.net',
      url='http://www.xwaves.net',
      ext_modules = [module1],
     )
