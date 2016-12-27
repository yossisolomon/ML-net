#!/usr/bin/python

import pandas as pd
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("-i","--in-file",required=True)
parser.add_argument("-o","--out-file")
parser.add_argument("-s","--shift",type=int,default=3)
args = parser.parse_args()
if args.out_file is None:
    args.out_file = args.in_file + "-shifted.out"

print("Shifting "+args.in_file+" by " + str(args.shift))
# In order to get the amount of cols
df = pd.read_csv(args.in_file,header=None)#,names=["col%d"%i for i in range(211)])

if args.shift==0:
    print("shift by 0 is just a copy")
else:
    df[0] = df[0].shift(-args.shift) # shifts first column args.shift times
    df.drop(df.index[-args.shift:], inplace=True) # removes first 3 rows (don't have the first column now
    df[0] = df[0].astype(int) # keep it integer-type:
    # Because of the shift there will be NaN values which only have a float implementation.
    # In order to stay with ints we need to convert it back...
df.to_csv(args.out_file,header=False,index=False)

