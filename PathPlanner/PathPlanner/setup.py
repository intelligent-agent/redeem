#!/usr/bin/env python

from distutils.core import setup, Extension

module1 = Extension('_pathplanner', sources = ['PathPlanner.i','Path.cpp', 'PathPlanner.cpp','Printer.cpp','PruTimer.cpp','prussdrv.cpp'],  swig_opts=['-c++','-builtin'], extra_compile_args = ['-std=c++0x','-g','-O0'])

setup(name='PathPlanner',
      version='1.0',
      description='PathPlanner for 3D printer',
      author='Mathieu Monney',
      author_email='zittix@xwaves.net',
      url='http://www.xwaves.net',
      ext_modules = [module1],
     )
