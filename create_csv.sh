#!/bin/bash

echo_headlines() {
  LINE=$(cat $1 | tail -n2 | head -n1)
  NEW_LINE=''
  for word in $LINE ; do 
    # check if this is one of the headlines (not a number, or the INFO logging statement)
    if [[ ${word:0:4} == INFO ]] ;
    then
      continue
    fi
    if ! [[ ${word:0:1} =~ [0-9] ]] ;
    then
      NEW_LINE=$NEW_LINE,$word
    fi
  done
  echo $NEW_LINE
}


echo_values() {
  for f in $@ ; do 
    LINE=$(cat $f | tail -n2 | head -n1)
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

echo_headlines $1
echo_values $@
