

'''
This script reads a .eeprom file and writes the content to the i2c eeprom
''' 
import os as os

filename ="Replicape.eeprom" 
eeprom_addr = "0x54"
with open(filename, 'r') as f:	
	for i, ch in enumerate(f.read()):
		cmd = "i2cset -y 3 "+eeprom_addr+" "+hex(i)+" 0x"+ch.encode("hex")
		os.system(cmd)
