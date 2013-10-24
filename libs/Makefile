#!/bin/bash

all: $(DIST)
	@echo "Done, now run 'source /etc/profile'"

angstrom:
	@echo "** Installing necessary packages **"
	opkg update
	opkg install python-email
	opkg install python-smbus
	opkg install python-distutils
	opkg install python-mmap
	opkg install python-profile
	@echo "** Installing SPI library **"
	cd spi && python setup.py install
	mkdir -p /usr/local/lib/
	@echo "** Installing PyPruss library **"
	git config --global http.sslVerify false
	git clone https://intelligentagent@bitbucket.org/intelligentagent/pypruss.git
	cd pypruss && python setup.py install
	cd pypruss/PASM/pasm_source/ && ./linuxbuild
	cp pypruss/PASM/pasm ../firmware/
	echo "export LD_LIBRARY_PATH=/usr/local/lib" >> /etc/profile


ubuntu:
	@echo "** Installing necessary packages **"
	apt-get update
	apt-get install python-dev
	apt-get install python-serial
	apt-get install python-numpy
	apt-get install python-smbus
	@echo "** Installing SPI library **"
	cd spi && python setup.py install
	@echo "** Installing PyPruss library **"
	mkdir -p /usr/local/lib/
	git clone https://intelligentagent@bitbucket.org/intelligentagent/pypruss.git
	cd pypruss && python setup.py install
	cp pypruss/pypruss/lib/libprussdrv.so /usr/local/lib/
	echo "export LD_LIBRARY_PATH=/usr/local/lib" >> /etc/profile

