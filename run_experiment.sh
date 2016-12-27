#!/bin/bash

set -e

if [[ -x $1 ]]
then
    echo Running experiment with $@
else
    echo Experiment file \"$1\" is not executable or found
    exit 1
fi
# make sure needed services are running
sudo /etc/init.d/ssh restart
sudo /etc/init.d/openvswitch-switch restart

# create experiment folder
EXP_DIR=~/ML-net/results/exp-`date  +%Y%m%d-%H%M%S`
mkdir -p $EXP_DIR

# run experiment
sudo EXP_DIR=$EXP_DIR $1
# cleanup mininet
sudo mn -c

# run decode
EXP_DIR=$EXP_DIR ./run_auto_decode.sh

# run analysis
EXP_DIR=$EXP_DIR ./run_auto_analysis.sh

echo The experiment files can be found in $EXP_DIR
