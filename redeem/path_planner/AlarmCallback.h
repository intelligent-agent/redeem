/*
This file is part of Redeem - 3D Printer control software

Redeem is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Redeem is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Redeem.  If not, see <http://www.gnu.org/licenses/>.

*/

#pragma once
#include <string>

class AlarmCallback
{
public:
  virtual void call(int alarmType, std::string message, std::string shortMessage);
  virtual ~AlarmCallback();
};