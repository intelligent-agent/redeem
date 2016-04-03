"""
PruInterface.py file for Replicape.

Handles direct manipulation of registers in Python-PRU.  

License: GNU GPL v3: http://www.gnu.org/copyleft/gpl.html

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

import os
import logging

import struct
import mmap

PRU_ICSS = 0x4A300000 
PRU_ICSS_LEN = 512*1024
SHARED_RAM_START = 0x00012000

# 

class PruInterface:
    @staticmethod
    def get_shared_long(offset):
        lon = [-1]
        with open("/dev/mem", "r+b") as f:
            ddr_mem = mmap.mmap(f.fileno(), PRU_ICSS_LEN, offset=PRU_ICSS)
            lon = struct.unpack('L', ddr_mem[SHARED_RAM_START+offset:SHARED_RAM_START + offset + 4])
        return lon[0]
        
    @staticmethod
    def set_shared_long(offset, L):
        with open("/dev/mem", "r+b") as f:
            ddr_mem = mmap.mmap(f.fileno(), PRU_ICSS_LEN, offset=PRU_ICSS)
            lon = struct.pack('L', L)
            ddr_mem[SHARED_RAM_START+offset:SHARED_RAM_START + offset + 4] = lon
        return
        
    @staticmethod
    def set_active_endstops(L):
        PruInterface.set_shared_long(8, L)
        return 
    
    @staticmethod
    def get_steps_remaining():
        return PruInterface.get_shared_long(16)
        
#        with open("/dev/mem", "r+b") as f:	       
#            ddr_mem = mmap.mmap(f.fileno(), PRU_ICSS_LEN, offset=PRU_ICSS) 
#            shared = struct.unpack('LLLL', ddr_mem[SHARED_RAM_START:SHARED_RAM_START+16])
#            steps_remaining = shared[3]
#        return steps_remaining