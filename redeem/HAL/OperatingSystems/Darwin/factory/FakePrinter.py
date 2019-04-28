#!/usr/bin/env python


class Printer(object):
  def __init__(self, path, name):
    print("{} Printer".format(name))


class FakePrinter_None(Printer):
  def __init__(self, path):
    super().__init__(path, "Fake")
