
FILENAME=firmware_runtime
FILENAME_ENDSTOPS=firmware_endstops

.PHONY: clean all

all: A3 A4
		

A3:		compiler
	pasm -b -DREV_A3 $(FILENAME).p
	pasm -b -DREV_A3 $(FILENAME_ENDSTOPS).p
	mv $(FILENAME).bin $(FILENAME)_00A3.bin
	mv $(FILENAME_ENDSTOPS).bin $(FILENAME_ENDSTOPS)_00A3.bin
A4:		compiler
	pasm -b -DREV_A4 $(FILENAME).p
	pasm -b -DREV_A4 $(FILENAME_ENDSTOPS).p
	mv $(FILENAME).bin $(FILENAME)_00A4.bin
	mv $(FILENAME_ENDSTOPS).bin $(FILENAME_ENDSTOPS)_00A3.bin

compiler:
	if [ ! -f pasm ]; then make -C pasm_source; fi

clean: 
	rm -f $(FILENAME)_00A3.bin
	rm -f $(FILENAME)_00A4.bin



