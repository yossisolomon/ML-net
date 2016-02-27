#!/bin/bash

if [[ -f $1 ]]
then
    echo Running experiment with $1
else
    echo Experiment file \"$1\" is not a file or found
    exit 1
fi

EXP_PY=/tmp/ML-topo.py
# generate experiment
./topology-creator/GraphML-Topo-to-Mininet-Network-Generator.py -i $1 -o $EXP_PY

# run experiment
sudo $EXP_PY
# cleanup mininet
sudo mn -c