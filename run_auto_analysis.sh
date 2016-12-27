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
TIMESHIFTS="${TIMESHIFTS:-0}"

for csv in `ls $ANALYSIS_DIR/*.csv` ; do
    echo Running SVM analysis for $csv with TIMESHIFTS=$TIMESHIFTS 
    CHECK=`~/ML-net/check_result.sh $csv`
    echo $CHECK
    if [[  $(echo $CHECK | grep -c "Overload=0") -gt 0 ]]
    then
      echo Skipping this file\'s ML analysis - no overloaded samples
    else
      timeshift=0
      while [ $timeshift -le $TIMESHIFTS ] ; do
        shiftedcsv=$csv.shift$timeshift
        python ~/ML-net/shift_first_column.py -i $csv -o $shiftedcsv -s $timeshift
        csv=$shiftedcsv
        echo Analysing CSV shifted by $timeshift in $csv
        python ~/ML-net/auto_switch_svm.py -i $csv --write-each-class-results &> $csv.result 
        timeshift=$(($timeshift+1))
      done
    fi
done

echo The analysis files can be found in $ANALYSIS_DIR
