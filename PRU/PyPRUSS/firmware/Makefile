

all:
	../PASM/pasm -b firmware_PRU0.p
	../PASM/pasm -b firmware_PRU1.p

install: 
	cp firmware_PRU0.bin ../
	cp firmware_PRU1.bin ../

clean:
	rm -rf firmware_PRU0.bin firmware_PRU1.bin
