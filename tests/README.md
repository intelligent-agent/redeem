# Unit Testing

Redeem was originally written in, "code first, test later" fashion. Unit testing began to be retro fitted in June 2017.

In order to run this test module, run `python -m unittest discover tests` from parent directory.

This test platform supports execution outside of a physical Beagle Bone Black, say on a local Linux ia64 or whatever.

A virtual environment is recommended. Example set-up for testing only ...

```
$ sudo apt install virtualenv
$ cd <path to your cloned redeem>/tests
tests$ virtualenv --no-site-packages venv
tests$ source venv/bin/activate
(venv) tests$ pip install -r module_requirements.txt
...
...
(venv) tests$ pytest
======================== test session starts =========================
platform linux2 -- Python 2.7.12, pytest-3.1.2, py-1.4.34, pluggy-0.4.0
rootdir: /home/bryan/projects/redeem, inifile:
collected 32 items 

gcode/test_G1_G0.py ...
gcode/test_G20_G21.py ..
gcode/test_G28.py ...
gcode/test_Gcode.py ........................

===================== 32 passed in 0.20 seconds ======================

```

If running tests on the BeagleBone, which has limited storage, it's probably best to skip the virtual environment and go straight to `pip install -r module_requirements.txt`.

