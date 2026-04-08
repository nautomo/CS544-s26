FROM p5-base

CMD ["/bin/bash", "-c", "/spark-4.1.1-bin-hadoop3/sbin/start-worker.sh spark://boss:7077 -c 2 -m 2g && tail -f /dev/null"]
