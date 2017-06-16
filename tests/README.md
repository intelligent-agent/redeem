# Unit Testing

To run all unit tests for Redeem, change to the `/usr/src/redeem/tests` folder and execute `pytests -v`. (The `-v` is optional.)

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
gcode/test_gcode.py::GcodeTest::test_gcode_get_answer PASSED
gcode/test_gcode.py::GcodeTest::test_gcode_get_distance_by_letter PASSED
gcode/test_gcode.py::GcodeTest::test_gcode_get_float_by_letter PASSED
gcode/test_gcode.py::GcodeTest::test_gcode_get_int_by_letter PASSED
gcode/test_gcode.py::GcodeTest::test_gcode_get_message PASSED
gcode/test_gcode.py::GcodeTest::test_gcode_get_token_index_by_letter PASSED
gcode/test_gcode.py::GcodeTest::test_gcode_get_tokens PASSED
gcode/test_gcode.py::GcodeTest::test_gcode_get_tokens_as_dict PASSED
gcode/test_gcode.py::GcodeTest::test_gcode_has_letter PASSED
gcode/test_gcode.py::GcodeTest::test_gcode_has_letter_value PASSED
gcode/test_gcode.py::GcodeTest::test_gcode_has_value PASSED
gcode/test_gcode.py::GcodeTest::test_gcode_is_crc PASSED
gcode/test_gcode.py::GcodeTest::test_gcode_is_info_command PASSED
gcode/test_gcode.py::GcodeTest::test_gcode_is_valid PASSED
gcode/test_gcode.py::GcodeTest::test_gcode_num_tokens PASSED
gcode/test_gcode.py::GcodeTest::test_gcode_parser PASSED
gcode/test_gcode.py::GcodeTest::test_gcode_remove_token_by_letter PASSED
gcode/test_gcode.py::GcodeTest::test_gcode_set_answer PASSED
gcode/test_gcode.py::GcodeTest::test_gcode_set_tokens PASSED
gcode/test_gcode.py::GcodeTest::test_gcode_token_distance PASSED
gcode/test_gcode.py::GcodeTest::test_gcode_token_letter PASSED
gcode/test_gcode.py::GcodeTest::test_token_value PASSED

========================== 24 passed in 1.02 seconds ===========================
```

