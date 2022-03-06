#!/bin/bash
	    for ngram in 1 2 3
	      do
		      for bd in 0.5 0.7 0.8 0.85 0.9 0.95 0.99
		        do
		        for wbd in 0.4 0.5 0.6 0.7 0.8 0.9 0.99
			        do
			          echo -e "$ngram $bd $wbd: $(python3 twitter_learn_weights.py $ngram $bd $wbd)"
              done
            done
          done