#!/bin/bash

set -e

if [ ! -z "$EXP_DIR" ]
then
    echo Running automatic analysis with $EXP_DIR
else
    echo Experiment directory \(EXP_DIR env var\) is not set
    exit 1
fi

ANALYSIS_DIR=$EXP_DIR/sax_analysis
mkdir -p $ANALYSIS_DIR

DECODE_FOR_SAX_RESULT=$ANALYSIS_DIR/decoded-exp-result-for-sax.csv
~/ML-net/decode_to_sax.py -i $EXP_DIR -o $DECODE_FOR_SAX_RESULT &> $ANALYSIS_DIR/decode_to_sax.log

SAX_SYMBOLS=4
#Current sample count (4 hours), should add better support via experiment output
SAX_RESULT=$ANALYSIS_DIR/decoded-exp-result-for-sax.csv
java -jar spmf.jar run Convert_time_series_to_sequence_database_using_SAX $DECODE_RESULT $SAX_RESULT $EXP_SAMPLE_COUNT $SAX_SYMBOLS , true

~/ML-net/decode_sax.py -i $SAX_RESULT -o  &> $ANALYSIS_DIR/decode_sax.log

DECODE_ERMINER_RESULT=$ANALYSIS_DIR/decoded-exp-erminer-result.txt

java -jar spmf.jar run ERMiner $SAX_RESULT $DECODE_ERMINER_RESULT 75% 50%

echo The decoded file can be found in $ANALYSIS_DIR
