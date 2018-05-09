#!/bin/bash

GRAPHML=$1
shift

if [[ -f $GRAPHML ]]
then
    echo Running experiment with $GRAPHML
else
    echo Experiment file \"$GRAPHML\" is not a file or found
    exit 1
fi

EXP_PY=/tmp/`basename $GRAPHML`-topo.py
# generate experiment
./topology-creator/GraphML-Topo-to-Mininet-Network-Generator.py -i $GRAPHML -o $EXP_PY -c 127.0.0.1

# run experiment
./run_experiment.sh $EXP_PY
