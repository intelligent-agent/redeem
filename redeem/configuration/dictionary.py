'''
Global Configuration Options

Author: Richard Wackerbarth
email: rkw(at)dataplex(dot)net
License: GNU GPL v3: http://www.gnu.org/copyleft/gpl.html
Copyright: (C) 2019  Richard Wackerbarth

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''

CONFIGURATION_VERSION = 1

class Settings:
  _shared_state = {}

  def __init__(self):
    self.__dict__ = self._shared_state

  def get_section(self, key):
    if key in self.__dict__:
      return self.__dict__[key]
    else:
      return None

  def get(self, section, key):
    try:
      value = self.__dict__[section][key]
    except KeyError:
      value = None
    return value

  def has_section(self, section):
    try:
      self.__dict__[section]
      return True
    except:
      return False

  def add_section(self, section):
    if not self.has_section(section):
      self.__dict__[section] = {}
    return self.__dict__[section]

  def put(self, section, key, value):
    self.add_section(section)[key] = str(value)
    return value

  def __str__(self):
    return self.__dict__.__str__()

  def clear(self):
    for section in list(self.__dict__):
      # Pop each section
      self.__dict__.pop(section)

  def pop(self, section, key):
    try:
      self.__dict__[section].pop(key)
    except KeyError:
      pass

  def merge(self, overlay):
    for section in overlay:
      for key in overlay[section]:
        value = overlay[section][key]
        self.put(section, key, value)

class ConfiguredSettings(Settings):
  _shared_state = {}

  def __init__(self):
    self.__dict__ = self._shared_state


class LocalizedSettings(Settings):
  _shared_state = {}

  def __init__(self):
    self.__dict__ = self._shared_state

  def get(self, section, key):
    try:
      return self.__dict__[section][key]
    except TypeError:
      return ConfiguredSettings().get(section, key)

  def save(self):
    with open(self._local_config_dir_path, 'w') as f:
      f.write("### Localized Configuration\n[Configuration]\nversion = {}\n".format(CONFIGURATION_VERSION))
      for section in self.__dict__:
        if section not in {'Configuration', 'Hogwash'}:
          if len(section) > 0:
            f.write("\n[{}]\n".format(section))
            for key in self.__dict__[section]:
              value = self.__dict__[section][key]
              f.write("{} = {}\n".format(key, value))

  def set_config_directory(self, path_to_directory):
    LocalizedSettings._local_config_dir_path = path_to_directory


class CurrentSettings(Settings):
  _shared_state = {}

  def __init__(self):
    self.__dict__ = self._shared_state

  def get(self, section, key):
    try:
      value = self.__dict__[section][key]
      return value
    except TypeError:
      value = LocalizedSettings().get(section, key)
      self.set(section, key, value)
      return value

  def save(self):
    for section in self.__dict__:
      for key in self.__dict__[section]:
        value = self.__dict__[section][key]
        # Purge it from Localized
        LocalizedSettings().pop(section, key)
        if value != ConfiguredSettings().get(section, key):
          # if it differs from Configured, preserve it in Localized
          LocalizedSettings().put(section, key, value)
    # and save the resulting Localized
    LocalizedSettings().save()
    self.clear()
