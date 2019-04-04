"""
GCode M360
Dump configuration 

Author: Elias Bakken
email: elias(at)iagent(dot)no
Website: http://www.thing-printer.com
License: GPLv3
"""
from __future__ import absolute_import

import json

from .GCodeCommand import GCodeCommand
from redeem.Alarm import Alarm


class M360(GCodeCommand):
  def execute(self, g):
    settings = self.printer.config.get_default_settings()
    # If no tokens are given, return the current settings
    if g.num_tokens() == 0:
      answer = "ok " + "\n".join([":".join(line) for line in settings])
      g.set_answer(answer)
    elif g.has_letter("U"):
      Alarm.action_command(
          "review_data",
          json.dumps({
              "type": "review_data",
              "message_title": "Config data ready",
              "message_text": "Click to upload and view",
              "message_type": "info",
              "message_hide": False,
              "data_type": "config_data",
              "replicape_key": self.printer.config.replicape_key,
              "data": settings
          }))

  def get_description(self):
    return "Get current config"

  def get_long_description(self):
    return ("Get current config")
