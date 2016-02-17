
FILENAME_RUNTIME=firmware_runtime
FILENAME_ENDSTOPS=firmware_endstops

.PHONY: clean all

all: compiler
	pasm -b $(FILENAME_RUNTIME).p
	pasm -b $(FILENAME_ENDSTOPS).p

compiler:
	if [ ! -f pasm ]; then make -C pasm_source; fi

clean: 
	rm -f $(FILENAME_RUNTIME).bin
	rm -f $(FILENAME_ENDSTOPS).bin



