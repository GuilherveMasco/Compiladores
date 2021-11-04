#!/bin/bash

for f in `ls *.tpp`; do 
  echo $f
  python3 tpplex.py $f > $f.out
done
