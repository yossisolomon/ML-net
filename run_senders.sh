#!/bin/bash

HOST_IP_ADDRESSES=`h=1 ; while (( $h <= $HOST_COUNT )) ; do echo 10.0.0.$((h++)) ; done`

for host_addr in $HOST_IP_ADDRESSES ; do
	HOST_CONF=$CONF_BASE/config-$host_addr
	#runuser is used because we are using sudo to run the experiment
	runuser -l tutorial1 -c "ssh tutorial1@$host_addr -o StrictHostKeyChecking=false ITGSend $HOST_CONF >/dev/null" &
done

wait

