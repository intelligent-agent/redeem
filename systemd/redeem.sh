#!/bin/sh

case $1 in 
	start)
		export LD_LIBRARY_PATH=/usr/local/lib
		cd /usr/src/redeem/software/ && python Redeem.py
		echo "Redeem started ok"
		exit 0
		;;
	stop)
		pkill -9 -f Redeem.py
		echo "Execed killall Redeem"
		;;
	*)
		echo "Usage: $0 {start|stop}"
esac
