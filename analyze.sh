#!/bin/bash
set -e

./gen_prompt.sh > /dev/null 2>&1

python3 - <<EOF > calculator/prompt.json
import json
print(json.dumps({"system_prompt": open("calculator/prompt.txt").read()}))
EOF

bash ./google_gemma-3-4b-it-Q6_K.llamafile \
  --system-prompt-file calculator/prompt.json \
  --silent-prompt \
  --log-disable \
  --temp 0 \
| fmt -w 80
