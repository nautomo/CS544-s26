FROM p5-base
CMD ["sh", "-c", "/spark-3.5.5-bin-hadoop3/sbin/start-worker.sh spark://boss:7077 -c 2 -m 2g && sleep infinity"]
