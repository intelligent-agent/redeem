"""
GCode M400
Wait until all buffered paths are executed

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

from .GCodeCommand import GCodeCommand
import logging
import threading


class M400(GCodeCommand):
  def execute(self, g):
    # nothing to do here - GCodeProcessor knows we're a buffered GCode, so it'll force the queues to sync before starting us
    logging.info("M400 executed")

  def get_description(self):
    return "Wait until all buffered paths are executed"

  def is_buffered(self):
    return True
