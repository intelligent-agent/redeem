

all:
	cp redeem.sh /etc/init.d/
	cp redeem.service /lib/systemd/system/
	systemctl enable redeem.service 
	cp tty0tty.sh /etc/init.d/
	chmod +x /etc/init.d/tty0tty.sh
	cp tty0tty.service /lib/systemd/system/
	systemctl enable tty0tty.service 
	

