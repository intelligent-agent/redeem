import logging
import os
import sys

class ConfigurationFiles(list):
  _shared_state = None

  def __new__(cls):
    if ConfigurationFiles._shared_state == None:
      obj = super().__new__(cls)
      ConfigurationFiles._shared_state = obj
    return ConfigurationFiles._shared_state

  def append(self, a_config_file_path):
    logging.info("Considering {}".format(a_config_file_path))
    if os.path.exists(a_config_file_path):
      super().append(a_config_file_path)


ConfigurationFileList = ConfigurationFiles()

from .dictionary import ConfiguredSettings, LocalizedSettings, CurrentSettings

# Capture the command line information
for token in sys.argv:
  if token == '--project_select':
    ConfiguredSettings.set('Software', 'selectable', True)

from .safe import safe_configuration
from .standard import standard_configuration
from .dictionary import ConfiguredSettings, LocalizedSettings, CurrentSettings

print(os.path.basename(__file__))
