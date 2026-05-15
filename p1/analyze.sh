#!/bin/bash
set -e

./gen_prompt.sh > /dev/null 2>&1

bash ./google_gemma-3-4b-it-Q6_K.llamafile \
  -f calculator/prompt.txt \
  --silent-prompt \
  --log-disable \
  --temp 0 \
| fmt -w 80
