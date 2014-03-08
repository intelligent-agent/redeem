
FILENAME=firmware

.PHONY: clean all

all: A3 A4
		

A3:
		pasm -b -DREV_A3 $(FILENAME).p
		mv $(FILENAME).bin $(FILENAME)_00A3.bin
A4:
		pasm -b -DREV_A4 $(FILENAME).p
		mv $(FILENAME).bin $(FILENAME)_00A4.bin

clean: 
		rm -f $(FILENAME)_00A3.bin
		rm -f $(FILENAME)_00A4.bin



