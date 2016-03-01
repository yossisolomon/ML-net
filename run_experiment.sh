#!/bin/bash

set -e

if [[ -x $1 ]]
then
    echo Running experiment with $1
else
    echo Experiment file \"$1\" is not executable or found
    exit 1
fi

# create experiment folder
EXP_DIR=~/ML-net/results/exp-`date  +%H%M%S-%d%m%Y`
mkdir -p $EXP_DIR
echo The experiment files can be found in $EXP_DIR

# run experiment
sudo EXP_DIR=$EXP_DIR $1
# cleanup mininet
sudo mn -c

ANALYSIS_DIR=$EXP_DIR/analysis
mkdir -p $ANALYSIS_DIR
~/ML-net/decode.py -i $EXP_DIR -o $ANALYSIS_DIR
for csv in `ls $ANALYSIS_DIR/*.csv` ; do
    echo Running SVM analysis for $csv ;
    ~/ML-net/check_result.sh $csv ;
    python ~/ML-net/switch_svm.py -i $csv --write-each-class-results &> $csv.result ;
done
