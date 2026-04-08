FROM p5-base

CMD ["/bin/bash", "-c", "/spark-4.1.1-bin-hadoop3/sbin/start-master.sh && tail -f /dev/null"]
