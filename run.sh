#!/bin/bash
# random delay between 5 and 10 minutes
MIN=0   # 0 minutes
MAX=900   # 15 minutes

set -e
cd /Users/vitalii.lebedynskyi/Projects/yelly_sniffer || exit 1

DELAY=$(( RANDOM % (MAX - MIN + 1) + MIN ))
sleep "$DELAY"

source .venv/bin/activate
python main.py -x -f -s https://dzen.ru/eg_moi_istorii,https://dzen.ru/id/622ce7c8811d761462ef111a,https://dzen.ru/verynevery