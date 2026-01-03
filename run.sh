# random delay between 5 and 10 minutes
MIN=0   # 0 minutes
MAX=900   # 15 minutes

DELAY=$(( RANDOM % (MAX - MIN + 1) + MIN ))
sleep "$DELAY"

source .venv/bin/activate
python main.py -s https://dzen.ru/historygothy,https://dzen.ru/eg_moi_istorii,https://dzen.ru/russianfood.com,https://dzen.ru/id/5aa3c26577d0e63329b9eaf3  -x -f
