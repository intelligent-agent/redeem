# Makefile for flashing the eeprom of the Replicape

all:
	node ./eeprom.js -w replicape_00A2.json
	cat Replicape.eeprom > /sys/bus/i2c/drivers/at24/1-0055/eeprom
