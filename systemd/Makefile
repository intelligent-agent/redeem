

all:
	cp replicape.sh /etc/init.d/
	cp replicape.service /lib/systemd/system/
	systemctl enable replicape.service 
	cp tty0tty.sh /etc/init.d/
	chmod +x /etc/init.d/tty0tty.sh
	cp tty0tty.service /lib/systemd/system/
	systemctl enable tty0tty.service 
	

