#!/usr/bin/env python

from distutils.core import setup, Extension

import os
from distutils.sysconfig import get_config_vars

(opt,) = get_config_vars('OPT')
os.environ['OPT'] = " ".join(
    flag for flag in opt.split() if flag != '-Wstrict-prototypes'
)



pathplanner = Extension('_PathPlannerNative', 
    sources = ['PathPlannerNative.i', 
                'PathPlanner.cpp', 
                'PathPlannerSetup.cpp',
                'Preprocessor.cpp',
                'Path.cpp', 
                'Delta.cpp',
                'vector3.cpp',
                'PruTimer.cpp',
                'prussdrv.c',
                'Logger.cpp'],  
    swig_opts=['-c++','-builtin'], 
    extra_compile_args = [
        '-std=c++0x',
        '-g',
        '-Ofast',
        '-fpermissive',
        '-D_GLIBCXX_USE_NANOSLEEP',
        '-DBUILD_PYTHON_EXT=1', 
        '-Wno-write-strings', 
        '-Wno-maybe-uninitialized', 
    	'-Wno-format', 
	'-DDEBUG=1'])

setup(name='PathPlannerNative',
      version='1.0',
      description='PathPlanner for 3D printer',
      author='Mathieu Monney',
      author_email='zittix@xwaves.net',
      url='http://www.xwaves.net',
      ext_modules = [pathplanner],
     )
