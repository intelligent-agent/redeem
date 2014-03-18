import pypruss								# The Programmable Realtime Unit Library
import struct
import mmap
import time


PRU_ICSS = 0x4A300000 
PRU_ICSS_LEN = 512*1024

RAM0_START = 0x00000000
RAM1_START = 0x00002000
RAM2_START = 0x00012000

pypruss.init()								# Init the PRU
pypruss.open(0)                                 # Open PRU event 0 which is PRU0_ARM_INTERRUPT
pypruss.pruintc_init()						# Init the interrupt controller
pypruss.exec_program(1, "../firmware/firmware_endstops.bin")	# Load firmware "mem_write.bin" on PRU 0

with open("/dev/mem", "r+b") as f:	       
    ddr_mem = mmap.mmap(f.fileno(), PRU_ICSS_LEN, offset=PRU_ICSS) 
    while True: 
        shared = struct.unpack('LLL', ddr_mem[RAM2_START:RAM2_START+12])
        print "Raw: "+bin(shared[0])+" Masked: "+bin(shared[1])+" Allowed: "+bin(shared[2])+(" "*30)+"\r", 

pypruss.exit()								# Exit




