

RPATH=/opt/Replicape
REMOTE=root@10.24.2.90
#REMOTE=root@192.168.7.2
DPATH=Dist/dist_`date +"%y_%m_%d"`/Replicape
DNAME=Replicape_rev_A4-`date +"%y_%m_%d"`.tgz

.PHONY : software firmware eeprom systemd

eeprom:
	scp eeprom/replicape_*.json eeprom/bone.js eeprom/eeprom.js eeprom/Makefile $(REMOTE):$(RPATH)/eeprom
	ssh $(REMOTE) 'cd /opt/Replicape/eeprom; make'

dt: 
	scp Device_tree/* $(REMOTE):$(RPATH)/device_tree/

systemd:
	scp systemd/* $(REMOTE):$(RPATH)/systemd/

software:
	scp software/*.py software/*.c $(REMOTE):$(RPATH)/software

config:
	scp -r software/config $(REMOTE):$(RPATH)/software

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

paddock: 
	scp Printrun/paddock.py $(REMOTE):$(RPATH)/software/

dist: 
	mkdir -p $(DPATH)
	mkdir -p $(DPATH)/software
	mkdir -p $(DPATH)/firmware
	mkdir -p $(DPATH)/device_tree
	mkdir -p $(DPATH)/eeprom
	mkdir -p $(DPATH)/libs/pypruss
	mkdir -p $(DPATH)/kernel
	cp Dist/Makefile $(DPATH)/
	cp software/*.py software/*.c $(DPATH)/software/
	cp -r software/config $(DPATH)/software/
	cp firmware/firmware_00A3.p firmware/Makefile firmware/pasm $(DPATH)/firmware/
	cp Device_tree/* $(DPATH)/device_tree/
	cp eeprom/eeprom.js eeprom/bone.js eeprom/replicape_*.json eeprom/Makefile $(DPATH)/eeprom/
	cp -r libs/spi $(DPATH)/libs/
	cp -r libs/i2c $(DPATH)/libs/
	cp libs/Makefile $(DPATH)/libs/
	cp -r images/3.8.13/* $(DPATH)/kernel/
	cp -r systemd $(DPATH)/
	cp -r tty0tty $(DPATH)/
	cd $(DPATH)/../ && tar -cvzpf ../$(DNAME) . && cd ..
	scp Dist/$(DNAME) replicape@scp.domeneshop.no:www/distros/
	
