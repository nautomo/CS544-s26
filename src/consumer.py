import os, sys, json
import pandas as pd
from kafka import KafkaConsumer, TopicPartition
from subprocess import check_output
import report_pb2

os.environ["CLASSPATH"] = str(check_output([os.environ["HADOOP_HOME"] + "/bin/hdfs", "classpath", "--glob"]), "utf-8")

BROKER = "localhost:9092"
TOPIC = "stock_prices"
HDFS_PATH = "hdfs://boss:9000/data"


def ensure_hdfs_dir():
    os.system(f"hdfs dfs -mkdir -p {HDFS_PATH}")


def load_checkpoint(partition):
    path = f"/src/partition-{partition}.json"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


def save_checkpoint(partition, batch_id, offset):
    path = f"/src/partition-{partition}.json"
    with open(path, "w") as f:
        json.dump({
            "batch_id": batch_id,
            "offset": offset
        }, f)


def main():
    if len(sys.argv) != 2:
        print("Usage: python consumer.py <partition_number>")
        sys.exit(1)

    partition_id = int(sys.argv[1])
    tp = TopicPartition(TOPIC, partition_id)

    consumer = KafkaConsumer(
        bootstrap_servers=BROKER,
        enable_auto_commit=False
    )

    consumer.assign([tp])

    checkpoint = load_checkpoint(partition_id)

    if checkpoint:
        batch_id = checkpoint["batch_id"] + 1
        consumer.seek(tp, checkpoint["offset"])
    else:
        batch_id = 0
        consumer.seek(tp, 0)

    ensure_hdfs_dir()

    while True:
        records = consumer.poll(timeout_ms=5000)

        if not records:
            continue

        rows = []

        for record in records.get(tp, []):
            r = report_pb2.Report()
            r.ParseFromString(record.value)

            rows.append({
                "ticker": r.ticker,
                "date": r.date,
                "price": r.price
            })

        if not rows:
            continue

        df = pd.DataFrame(rows)

        file_path = f"{HDFS_PATH}/partition-{partition_id}-batch-{batch_id}.parquet"

        df.to_parquet(file_path, engine="pyarrow", index=False)

        # checkpoint AFTER write
        offset = consumer.position(tp)
        save_checkpoint(partition_id, batch_id, offset)

        batch_id += 1


if __name__ == "__main__":
    main()
