#!/bin/sh

# Tiny script that re-lunches ITGRecv in case it dies...
while [ 1 ]
do
	date=`date`

	echo "-------------------------------"
	echo "[$date] Starting ITGRecv"
	ITGRecv -l /dev/null < /dev/null &
        wait

	echo "ITGRecv has crashed on: $date"

	sleep 1
done
