#!/bin/bash

# see how many hosts there are
export HOST_COUNT=`pgrep -c ITGRecv.sh`
if (( $HOST_COUNT == 0 )) ; then echo "Topology isn't online - no hosts found" ; exit 1 ; fi
# decide on configuration base path
export CONF_BASE="$EXP_DIR/config"
# generate config files for senders
./generate_config.py -d $CONF_BASE -n $HOST_COUNT
exit 0
# create list of interfaces + indexes (ifIndex)
ip a | sed '/^ / d' - | cut -d: -f1,2 > $EXP_DIR/intfs-list
# turn on sflow
./set_ovs_sflow.sh
# start collecting sflow datagrams
sflowtool -k &> $EXP_DIR/sflow-datagrams &
# run the senders of flows to dest
./run_senders.sh
# stop datagram collection
pkill -15 sflow

