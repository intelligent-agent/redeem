

#RPATH=/home/root/replicape
#REMOTE=root@10.24.2.124
RPATH=/root/replicape
REMOTE=root@10.24.2.85

.PHONY : software firmware eeprom

eeprom:
	scp eeprom/replicape.json  eeprom/eeprom.js Makefile $(REMOTE):$(RPATH)/eeprom
	ssh $(REMOTE) 'cd Replicape/eeprom; make eeprom_cat'

eeprom_upload: 
	node ./eeprom.js -w replicape.json
	python eeprom_upload.py

eeprom_cat:
	node ./eeprom.js -w replicape.json
	cat Replicape.eeprom > /sys/bus/i2c/drivers/at24/3-0055/eeprom

software:
	scp software/*.py $(REMOTE):$(RPATH)/software

gui: 
	scp -r software/gui/ $(REMOTE):$(RPATH)/software

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

install_image: 
	cp images/uImage-3.2.34-20130303 /boot/
	rm /boot/uImage
	ln -s /boot/uImage-3.2.34-20130303 /boot/uImage

install_modules: 
	unzip images/3.2.34.zip
	cp -r images/3.2.34/ /lib/modules/ 