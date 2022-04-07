#!/bin/bash
for ngram in 1 2 3
do
	for bd in 0.5 0.7 0.8 0.85 0.9 0.95 0.99
	do
		for wbd in 0.4 0.5 0.6 0.7 0.8 0.9 0.99
		do
		  for mp in 0 0.01 0.02 0.03 0.04 0.05 0.1 0.2
		  do
		    for wmp in 0 0.01 0.02 0.03 0.04 0.05 0.1 0.2
		    do
			    echo -e "$ngram $bd $wbd $mp $wmp: $(python3 twitter_learn_weights.py $ngram $bd $wbd $mp $wmp)"
        done
      done
    done
  done
done
