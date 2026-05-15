import os
import time
from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import UnknownTopicOrPartitionError
from sqlalchemy import create_engine, text
import report_pb2

PROJECT = os.environ["PROJECT"]
MYSQL_HOST = f"{PROJECT}-mysql-1"

DB_URI = f"mysql+mysqlconnector://root:abc@{MYSQL_HOST}:3306/CS544"

TOPIC = "stock_prices"
BROKER = "localhost:9092"


def init_topic():
    admin = KafkaAdminClient(bootstrap_servers=BROKER)

    try:
        admin.delete_topics([TOPIC])
        time.sleep(3)
    except UnknownTopicOrPartitionError:
        pass

    while True:
        try:
            admin.create_topics([
                NewTopic(name=TOPIC, num_partitions=4, replication_factor=1)
            ])
            break
        except Exception:
            time.sleep(1)

def main():
    print("PRODUCER STARTED", flush=True)
    init_topic()

    engine = create_engine(DB_URI, pool_pre_ping=True)

    producer = KafkaProducer(
        bootstrap_servers=BROKER,
        acks='all',
        retries=10
    )

    last_id = 0

    while True:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, ticker, date, price FROM stock_prices WHERE id > :id ORDER BY id ASC"),
                {"id": last_id}
            )

            rows = result.fetchall()

        if not rows:
            print("no rows")
            time.sleep(0.01)
            continue

        for row in rows:
            print("entered loop")
            last_id = row.id

            report = report_pb2.Report()
            report.date = str(row.date)
            report.price = float(row.price)
            report.ticker = row.ticker

            print(f"SENDING {row.ticker} {row.price}", flush=True)
            producer.send(
                TOPIC,
                key=row.ticker.encode(),
                value=report.SerializeToString()
            )
            print("producer sent?")

        producer.flush()
        print("producer flushed?")
        time.sleep(0.01)


if __name__ == "__main__":
    main()
