#!/bin/bash

HOST_IP_ADDRESSES=`h=1 ; while (( $h <= $HOST_COUNT )) ; do echo 10.0.0.$((h++)) ; done`

for host_addr in $HOST_IP_ADDRESSES ; do
	HOST_CONF=$CONF_BASE/config-$host_addr

	ssh $host_addr -o StrictHostKeyChecking=false $HOST_CONF > /dev/null &
done

wait

