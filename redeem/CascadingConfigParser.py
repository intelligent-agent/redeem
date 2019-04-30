'''
This is a temporary proxy to be phased out

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

import redeem.configuration as TheSystem

class CascadingConfigParser():
  def __init__(self, config_files):
    pass

  def get(self, section, key):
    return TheSystem.CurrentSettings().get(section, key)
    
  def set(self, section, key, value):
    TheSystem.CurrentSettings().put(section, key, value)