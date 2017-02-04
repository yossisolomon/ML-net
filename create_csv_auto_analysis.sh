#!/bin/bash

echo_headlines() {
  LINE=$(cat $1 | tail -n2 | head -n1 | cut -d" " -f5-24)
  NEW_LINE=''
  for word in $LINE ; do 
    if ! [[ ${word:0:1} =~ [0-9] ]] ;
    then
      NEW_LINE=$NEW_LINE,$word
    fi
  done
  echo $NEW_LINE
}


echo_values() {
  for f in $@ ; do 
    LINE=$(cat $f | tail -n2 | head -n1 | cut -d" " -f5-24)
    NEW_LINE=$(basename $f | sed -e 's/.csv.result//g' -e 's/sflow-//g')
    for word in $LINE ; do 
      # remove commas
      word=$(echo $word | sed -e 's/,//g')
      # check if this is one of the values (a number)
      if [[ ${word:0:1} =~ [0-9] ]] ;
      then
        NEW_LINE=$NEW_LINE,$word
      fi
    done
    echo $NEW_LINE
  done
}

echo_ensembles() {
  for f in $@ ; do
    echo grepping
    CONTENT=$(grep -B2 -e \'classifier:__choice__ -e MyDummy $f)
    NUM=0
    CLASSIFIER="Dummy"
    for word in $CONTENT ; do
      echo $word
      if [[ ${word:0:2} == "[(" ]] ; then
        NUM=${word:2:6}
      elif [[ ${word:0:1} == "(" ]] ; then
        NUM=${word:1:5}
      fi
    done
    echo $NUM
  done
}

echo_headlines $1
echo_values $@
#echo_ensembles $@
