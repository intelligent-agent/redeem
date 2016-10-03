from setuptools import setup, find_packages, Extension
import numpy as np
import os

from distutils.sysconfig import get_config_vars

# Remove the strict prototpyes warnings
(opt,) = get_config_vars('OPT')
os.environ['OPT'] = " ".join(
    flag for flag in opt.split() if flag != '-Wstrict-prototypes'
)


import os
from distutils.sysconfig import get_config_vars

(opt,) = get_config_vars('OPT')
os.environ['OPT'] = " ".join(
    flag for flag in opt.split() if flag != '-Wstrict-prototypes'
)



# Requirements for our application
# Note: WIP, not a complete list
INSTALL_REQUIRES = [
	"spidev==3.2.0", 
    "scipy",
    "numpy",
    "python-smbus"
]


pathplanner = Extension(
    '_PathPlannerNative', sources = [
        'redeem/path_planner/PathPlannerNative.i',
        'redeem/path_planner/PathPlanner.cpp',
        'redeem/path_planner/PathPlannerSetup.cpp',
        'redeem/path_planner/Preprocessor.cpp',
        'redeem/path_planner/Path.cpp',
        'redeem/path_planner/Delta.cpp',
        'redeem/path_planner/vector3.cpp',
        'redeem/path_planner/PruTimer.cpp',
        'redeem/path_planner/prussdrv.c',
        'redeem/path_planner/Logger.cpp'],
    swig_opts=['-c++','-builtin'],
    include_dirs = [np.get_include()],
    extra_compile_args = [
        '-std=c++0x',
        '-g',
        '-Ofast',
        '-fpermissive',
        '-D_GLIBCXX_USE_NANOSLEEP',
        '-DBUILD_PYTHON_EXT=1',
        '-Wno-write-strings',
        '-Wno-maybe-uninitialized']
)

setup(
    name = "Redeem",
    version = "1.2.8",
    packages = find_packages(exclude=["redeem/path_planner"]),
    data_files=[
        ('redeem/firmware', [
            'redeem/firmware/firmware_runtime.p',
            'redeem/firmware/firmware_endstops.p']),
        ('redeem/configs', [
            'configs/default.cfg',
            'configs/thing.cfg',
            'configs/makerbot_cupcake.cfg',
            'configs/maxcorexy.cfg',
            'configs/mendelmax.cfg',
            'configs/testing_rev_A.cfg',
            'configs/testing_rev_B.cfg',
            'configs/prusa_i3.cfg',
	        'configs/debrew.cfg',
	        'configs/kossel_mini.cfg',
            'configs/rostock_max_v2.cfg']),
        ('redeem/data',[
            'data/B57540G0104F000.cht',
            'data/B57560G104F.cht',
            'data/B57561G0103F000.cht',
            'data/QU-BD.cht',
            'data/HT100K3950.cht',
            'data/SEMITEC-104GT-2.cht',
            'data/DYZE500.cht',
            'data/E3D-PT100-AMPLIFIER.cht']),
    ],
    # metadata for upload to PyPI
    author = "Elias Bakken",
    author_email = "elias@iagent.no",
    description = "Replicape daemon",
    license = "GPLv3",
    keywords = "3d printer firmware",
    platforms = ["BeagleBone"],
    url = "https://bitbucket.org/intelligentagent/redeem",
    ext_modules = [pathplanner],
    entry_points = {
        'console_scripts': [
            'redeem = redeem.Redeem:main'
        ]
    },
    include_package_data = True
)
