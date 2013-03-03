

RPATH=/home/root/Replicape
REMOTE=root@10.24.2.124


.PHONY : software firmware eeprom

eeprom:
	scp tools/replicape.json tools/eeprom_upload.py eeprom/eeprom.js Makefile $(REMOTE):$(RPATH)/eeprom
	ssh $(REMOTE) 'cd Replicape/eeprom; make eeprom_cat'

eeprom_upload: 
	node ./eeprom.js -w replicape.json
	python eeprom_upload.py

eeprom_cat:
	node ./eeprom.js -w replicape.json
	cat Replicape.eeprom > /sys/bus/i2c/drivers/at24/3-0055/eeprom

software:
	scp software/*.py $(REMOTE):$(RPATH)/software

minicom:
	minicom -o -b 115200 -D /dev/ttyUSB1

firmware:
	scp -r firmware/ $(REMOTE):$(RPATH)
	ssh $(REMOTE) 'cd $(RPATH)/firmware; make'

pypruss: 
	scp -r PRU/PyPRUSS $(REMOTE):$(RPATH)/libs/
	ssh $(REMOTE) 'cd $(RPATH)/libs/PyPRUSS; make && make install'


tests:
	scp -r software/tests $(REMOTE):$(RPATH)/software/
