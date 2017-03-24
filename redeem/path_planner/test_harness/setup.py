#!/usr/bin/env python

from setuptools import setup, Extension

import os
from distutils.sysconfig import get_config_vars

(opt,) = get_config_vars('OPT')
os.environ['OPT'] = " ".join(
    flag for flag in opt.split() if flag != '-Wstrict-prototypes'
)

pathplanner = Extension('_PathPlannerMock', 
    sources = ['PathPlannerMock.i', 
                '../PathPlanner.cpp', 
                '../PathPlannerSetup.cpp',
                '../Preprocessor.cpp',
                '../Path.cpp', 
                '../Delta.cpp',
                '../vector3.cpp',
                '../vectorN.cpp',
                'MockPruTimer.cpp',
                'PruDump.cpp',
                '../Logger.cpp'],  
    swig_opts=['-c++','-builtin'], 
    extra_compile_args = [
        '-std=c++0x',
        '-g',
        '-O2',
        '-fpermissive',
        '-D_GLIBCXX_USE_NANOSLEEP',
        '-DBUILD_PYTHON_EXT=1', 
        '-Wno-write-strings', 
        '-Wno-maybe-uninitialized', 
        '-Wno-format',
        '-Werror',
        '-DDEBUG=1',
        '-UNDEBUG',
        '-D_GLIBCXX_DEBUG'])

setup(name='PathPlannerMock',
      version='1.0',
      description='PathPlanner for 3D printer',
      author='Mathieu Monney',
      author_email='zittix@xwaves.net',
      url='http://www.xwaves.net',
      ext_modules = [pathplanner],
	  test_suite="test"
     )
