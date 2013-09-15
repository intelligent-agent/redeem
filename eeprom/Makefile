# Makefile for flashing the eeprom of the Replicape


DIST=ubuntu
if [ -a /etc/angstrom-version ] ; \
then \
     DIST=angstrom ; \
fi;

all: $(DIST)

angstrom:
	node ./eeprom.js -w replicape_00A3.json
	cat Replicape.eeprom > /sys/bus/i2c/drivers/at24/1-0054/eeprom


ubuntu:
	sudo apt-get install nodejs
	nodejs ./eeprom.js -w replicape_00A3.json
	cat Replicape.eeprom > /sys/bus/i2c/drivers/at24/1-0054/eeprom
	
