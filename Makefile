

RPATH=/home/root/Replicape
REMOTE=root@192.168.7.2
DPATH=Dist/dist_`date +"%y_%m_%d"`/Replicape
DNAME=Replicape_rev_A2-`date +"%y_%m_%d"`.tgz

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
	scp -r software/GUI/ $(REMOTE):$(RPATH)/software

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

dist: 
	mkdir -p $(DPATH)
	mkdir -p $(DPATH)/software
	mkdir -p $(DPATH)/firmware
	mkdir -p $(DPATH)/device_tree
	mkdir -p $(DPATH)/eeprom
	mkdir -p $(DPATH)/libs/pypruss
	mkdir -p $(DPATH)/kernel
	cp Dist/Makefile $(DPATH)/
	cp software/*.py $(DPATH)/software/
	cp firmware/firmware_00A2.p firmware/Makefile firmware/pasm $(DPATH)/firmware/
	cp Device_tree/DTB/* $(DPATH)/device_tree/
	cp eeprom/eeprom.js eeprom/bone.js eeprom/replicape_00A2.json eeprom/Makefile $(DPATH)/eeprom/
	cp -r libs/spi $(DPATH)/libs/
	cp -r libs/pypruss/dist/* $(DPATH)/libs/pypruss
	cp -r libs/i2c $(DPATH)/libs/
	cp libs/Makefile $(DPATH)/libs/
	cp -r images/3.8.13/* $(DPATH)/kernel/
	cd $(DPATH)/../ && tar -cvzpf ../$(DNAME) . && cd ..
	scp Dist/$(DNAME) replicape@scp.domeneshop.no:www/distros/
	
