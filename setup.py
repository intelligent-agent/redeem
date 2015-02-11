from setuptools import setup, find_packages, Extension
import numpy as np

pathplanner = Extension(
    '_PathPlannerNative', sources = [
        'redeem/path_planner/PathPlannerNative.i',
        'redeem/path_planner/PathPlanner.cpp',
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
        '-DBUILD_PYTHON_EXT=1']
)

setup(
    name = "Redeem",
    version = "0.16.7",
    packages = find_packages(exclude=["redeem/path_planner"]),
    data_files=[
        ('redeem/firmware', [
            'redeem/firmware/config_00A4.h', 
            'redeem/firmware/config_00A3.h', 
            'redeem/firmware/firmware_runtime.p', 
            'redeem/firmware/firmware_endstops.p']),
        ('redeem/configs', [
            'configs/default.cfg', 
            'configs/Thing.cfg',
            'configs/Makerbot_cupcake.cfg', 
            'configs/MaxCoreXY.cfg', 
            'configs/MendelMax.cfg', 
            'configs/Testing.cfg', 
            'configs/Prusa.cfg',
	    'configs/Debrew.cfg', 
	    'configs/Delta.cfg'])
    ],
    # metadata for upload to PyPI
    author = "Elias Bakken",
    author_email = "elias.bakken@gmail.com",
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

