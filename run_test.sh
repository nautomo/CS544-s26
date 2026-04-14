export PROJECT=p6
docker compose up --build -d -t 0 --no-deps server1
docker exec ${PROJECT}-server1-1 python3 -m pytest rest_test.py -v
