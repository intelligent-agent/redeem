"""
Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: GNU GPL v3: http://www.gnu.org/copyleft/gpl.html

 This work in this file has been heavily influenced by the work of Steve Graves
 from his document on Delta printer kinematics: https://groups.google.com/forum/#!topic/deltabot/V6ATBdT43eU

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
"""

"""
This class is now used for holding all the parameters required to 
define a delta bot. All the actual computation is done within a 
C++ module within the NativePathPlanner class. See ./path_planner/Delta.*
for details.
"""


class Delta:
    Hez = 0.0601    # Distance head extends below the effector.
    L   = 0.322     # Length of the rod
    r   = 0.175    # Radius of the columns
    Ae  = 0.02032  # Effector offset
    Be  = 0.02032
    Ce  = 0.02032

    A_radial = 0.00            # Radius error of the named column                          
    B_radial = 0.00                                                                      
    C_radial = 0.00                                                                     
    A_tangential = 0.00                                                                 
    B_tangential = 0.00                                                                
    C_tangential = 0.00
