#!/bin/sh

case $1 in 
	start)
		/opt/Replicape/tty0tty/tty0tty > /var/log/tty0tty.log &
		echo "tty0tty started ok"
		exit 0
		;;
	stop)
		pkill -9 -f tty0tty
		echo "Killed tty0tty"
		;;
	*)
		echo "Usage: $0 {start|stop}"
esac
