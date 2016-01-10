#!/bin/bash

HOST_IP_ADDRESSES="10.0.0.1 10.0.0.2 10.0.0.3 10.0.0.4 10.0.0.5 10.0.0.6 10.0.0.7 10.0.0.8 10.0.0.9"
CONF_BASE="~/ML-net/config"

for host_addr in $HOST_IP_ADDRESSES ; do
	HOST_CONF="$CONF_BASE-$host_addr"
	ssh tutorial1@$host_addr -o StrictHostKeyChecking=false ITGSend $HOST_CONF >/dev/null &
done

wait

