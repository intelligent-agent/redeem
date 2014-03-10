# Compile the overlay and copy the files to the right dirs



all:
	dtc -O dtb -o BB-BONE-REPLICAP-00A3.dtbo -b 0 -@ BB-BONE-REPLICAP-00A3.dts
	dtc -O dtb -o BB-BONE-REPLICAP-00A4.dtbo -b 0 -@ BB-BONE-REPLICAP-00A4.dts
	cp BB-BONE-REPLICAP* /lib/firmware/
	cp am335x*.dtb /boot/
