# Unit Testing

To run all unit tests for Redeem, change to the `/usr/src/redeem/tests` folder and execute `pytests -v`. (The `-v` is optional.)

You'll need to install at least `pytest` and `testfixtures`. As `root` ...

```
# pip install pytest
# pip install testfixtures
```

If other packages are needed, you'll be told which ones when you try to run the tests.

Here's an example run from way back in June 2017 ...

```
root@kamikaze:/usr/src/redeem/tests# pytest -v
============================= test session starts ==============================
platform linux2 -- Python 2.7.12, pytest-3.1.2, py-1.4.34, pluggy-0.4.0 -- /usr/bin/python
cachedir: ../.cache
rootdir: /usr/src/redeem, inifile:
collected 24 items

gcode/test_gcode.py::GcodeTest::test_gcode__get_cs PASSED
gcode/test_gcode.py::GcodeTest::test_gcode_code PASSED
...
...
gcode/test_gcode.py::GcodeTest::test_gcode_token_letter PASSED
gcode/test_gcode.py::GcodeTest::test_token_value PASSED

========================== 24 passed in 1.02 seconds ===========================
```

