IP=10.24.2.129
UIMAGE=uImage-3.2.34-r18a+gitr720e07b4c1f687b61b147b31c698cb6816d72f01-beaglebone-20130112081401.bin
MODULES=modules-3.2.34-r18a+gitr720e07b4c1f687b61b147b31c698cb6816d72f01-beaglebone.tgz
IMG_PATH=/home/iagent/workspace/setup-scripts-replicape/build/tmp-angstrom_v2012_05-eglibc/deploy/images/beaglebone/
VERSION=3.2.34
PREV_VERSION=3.2.18

CMD =cd /tmp/; tar zxfv modules.tgz; # uncompress the modules
CMD+=mv /lib/modules /lib/modules-$(PREV_VERSION); mv /lib/firmware /lib/firmware-$(PREV_VERSION); # rename old verison
CMD+=mv lib/* /lib/ # Install new modules
 
image:
	scp $(IMG_PATH)$(UIMAGE) root@$(IP):/boot/uImage-$(VERSION)
	ssh root@$(IP) 'cd /boot/; rm uImage; ln -s uImage-$(VERSION) uImage'

modules: 
	scp $(IMG_PATH)$(MODULES) root@$(IP):/tmp/modules.tgz
	ssh root@$(IP) '$(CMD)'
	 
	
