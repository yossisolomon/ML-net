#!/bin/bash

# cleanup previous run
rm /tmp/intfs-list /tmp/sflow*
# create list of interfaces + indexes (ifIndex)
ip a | sed '/^ / d' - | cut -d: -f1,2 > /tmp/intfs-list
# turn on sflow
./set_ovs_sflow.sh
# start collecting sflow datagrams
sflowtool -k &> /tmp/sflow-datagrams &
# run the senders of flows to dest
./run_senders.sh
# stop the datgram collection
pkill -15 sflow

