#!/bin/bash

HOST_IP_ADDRESSES="10.0.0.1 10.0.0.2 10.0.0.3"
CONF_BASE="~/ML-net/config"

for host_addr in $HOST_IP_ADDRESSES ; do
	HOST_CONF="$CONF_BASE-$host_addr"
	ssh tutorial1@$host_addr -o StrictHostKeyChecking=false ITGSend $HOST_CONF >/dev/null &
done

wait

