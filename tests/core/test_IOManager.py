from __future__ import print_function
import mock
import unittest
import os
import threading
import select

#Make test version- agnostic:
from sys import version_info
if version_info.major == 2:
  import __builtin__ as builtins    # pylint:disable=import-error
else:
  import builtins    # pylint:disable=import-error

from IOManager import IOManager


class PipeWrapper:
  def __init__(self):
    read_fd, write_fd = os.pipe()
    print("pipe read_fd: " + str(read_fd))
    self.writer = os.fdopen(write_fd, 'w')
    self.reader = os.fdopen(read_fd, 'r')

  def send(self, msg):
    self.writer.write(msg)
    self.writer.flush()


class TestIOManager(unittest.TestCase):
  def setUp(self):
    self.manager = IOManager()

  def tearDown(self):
    if self.manager.is_running():
      self.manager.stop()

  def test_starts_and_stops(self):
    pass

  def test_is_running(self):
    self.assertTrue(self.manager.is_running())
    self.manager.stop()
    self.assertFalse(self.manager.is_running())

  def test_calls_callbacks(self):
    pipe = PipeWrapper()
    event = threading.Event()

    def callback(flag):
      if flag == select.POLLIN:
        text = pipe.reader.readline()
        if text == "super beans\n":
          event.set()
      else:
        self.assertEqual(flag, select.POLLHUP)

    self.manager.add_file(pipe.reader, lambda flag: callback(flag))

    self.assertFalse(event.is_set())
    pipe.send("super beans\n")
    event.wait(1)
    self.assertTrue(event.is_set())

  def test_removes_callbacks(self):
    pipe = PipeWrapper()
    event = threading.Event()

    def callback(flag):
      if flag == select.POLLIN:
        text = pipe.reader.readline()
        if text == "super beans\n":
          event.set()
      else:
        self.assertEqual(flag, select.POLLHUP)

    self.manager.add_file(pipe.reader, lambda flag: callback(flag))

    self.assertFalse(event.is_set())
    pipe.send("super beans\n")
    event.wait(1)
    self.assertTrue(event.is_set())

    event.clear()

    self.manager.remove_file(pipe.reader)

    self.assertFalse(event.is_set())
    pipe.send("super beans\n")
    event.wait(0.05)    # note that this will always be taken - the callback shouldn't fire
    self.assertFalse(event.is_set())

  def test_sends_hangups(self):
    pipe = PipeWrapper()
    event = threading.Event()

    def callback(flag):
      if flag != select.POLLHUP and flag != select.POLLNVAL:
        self.assertEqual(flag, select.POLLHUP | select.POLLNVAL)
      event.set()

    self.manager.add_file(pipe.reader, callback)
    pipe.writer.close()
    event.wait(1)
    self.assertTrue(event.is_set())
