#!/usr/bin/env python

from distutils.core import setup, Extension

import os
from distutils.sysconfig import get_config_vars

(opt, ) = get_config_vars('OPT')
os.environ['OPT'] = " ".join(flag for flag in opt.split() if flag != '-Wstrict-prototypes')

# yapf: disable
pathplanner = Extension(
    '_PathPlannerNative',
    sources=[
        'PathPlannerNative.i',
        'PathPlanner.cpp',
        'PathPlannerSetup.cpp',
        'Preprocessor.cpp',
        'Path.cpp',
        'Delta.cpp',
        'vector3.cpp',
        'vectorN.cpp',
        'PruTimer.cpp',
        'prussdrv.c',
        'Logger.cpp'
    ],
    swig_opts=['-c++', '-builtin', '-threads'],
    include_dirs=[np.get_include()],
    extra_compile_args=[
        '-std=c++0x',
        '-g',
        '-O3',
        '-fpermissive',
        '-flto',
        '-DBUILD_PYTHON_EXT=1',
        '-Wall',
    ])
# yapf: enable

setup(
    name='PathPlannerNative',
    version='1.0',
    description='PathPlanner for 3D printer',
    author='Mathieu Monney',
    author_email='zittix@xwaves.net',
    ext_modules=[pathplanner],
)
