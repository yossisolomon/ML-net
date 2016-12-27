#!/bin/bash

set -e

if [ ! -z "$EXP_DIR" ]
then
    echo Running automatic analysis with $EXP_DIR
else
    echo Experiment directory \(EXP_DIR env var\) is not set
    exit 1
fi

ANALYSIS_DIR=$EXP_DIR/auto_analysis
mkdir -p $ANALYSIS_DIR
~/ML-net/decode.py -i $EXP_DIR -o $ANALYSIS_DIR &> $ANALYSIS_DIR/decode.log

echo The decoded file can be found in $ANALYSIS_DIR
