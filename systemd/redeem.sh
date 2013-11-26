#!/bin/sh

case $1 in 
	start)
		export LD_LIBRARY_PATH=/usr/local/lib
		cd /opt/Replicape/software/ && python Replicape.py
		echo "Replicape started ok"
		exit 0
		;;
	stop)
		pkill -9 -f Replicape.py
		echo "Execed killall replicape"
		;;
	*)
		echo "Usage: $0 {start|stop}"
esac
