#!/bin/bash

overload=$( cat $1 | cut -d, -f1 | paste -sd+ | bc )
total=$( cat $1 | wc -l )
echo Total=$total Overload=$overload %=$(python -c "print($overload*1.0/$total)")
