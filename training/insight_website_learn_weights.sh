#!/bin/bash
for bd in 0.5 0.7 0.8 0.85 0.9 0.95 0.99
  do
	  echo -e "$bd: $(python3 insight_website_learn_weights.py 3 $bd)"
  done