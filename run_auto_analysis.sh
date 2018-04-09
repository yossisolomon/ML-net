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
TIMESHIFTS="${TIMESHIFTS:-10}"
CPU_NUM=$( grep processor /proc/cpuinfo | wc -l )
PARALLELISM=$(( $CPU_NUM / 2 ))
for csv in `ls $ANALYSIS_DIR/*.csv` ; do
    echo Running analysis for $csv with TIMESHIFTS=$TIMESHIFTS
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
        echo Analysing CSV shifted by $timeshift in $shiftedcsv
        sem -j$PARALLELISM --id $$ python ~/ML-net/auto_switch_ml.py -i $shiftedcsv &> $shiftedcsv.result
        timeshift=$(($timeshift+1))
      done
    fi
done

sem --wait --id $$

echo The analysis files can be found in $ANALYSIS_DIR
