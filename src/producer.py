import os
import time
from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import UnknownTopicOrPartitionError
from sqlalchemy import create_engine, text
import report_pb2

PROJECT = os.environ["PROJECT"]
MYSQL_HOST = f"{PROJECT}-mysql-1"

DB_URI = f"mysql+pymysql://root:abc@{MYSQL_HOST}:3306/CS544"

TOPIC = "stock_prices"
BROKER = "localhost:9092"


def init_topic():
    admin = KafkaAdminClient(bootstrap_servers=BROKER)

    try:
        admin.delete_topics([TOPIC])
        time.sleep(3)
    except UnknownTopicOrPartitionError:
        pass

    topic = NewTopic(name=TOPIC, num_partitions=4, replication_factor=1)
    admin.create_topics([topic])


def main():
    init_topic()

    engine = create_engine(DB_URI)

    producer = KafkaProducer(
        bootstrap_servers=BROKER,
        acks='all',
        retries=10
    )

    last_id = 0

    while True:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, ticker, date, price FROM stock_prices WHERE id > :id ORDER BY id ASC LIMIT 1000"),
                {"id": last_id}
            )

            rows = result.fetchall()

        if not rows:
            time.sleep(1)
            continue

        for row in rows:
            last_id = row.id

            report = report_pb2.Report()
            report.date = str(row.date)
            report.price = float(row.price)
            report.ticker = row.ticker

            producer.send(
                TOPIC,
                key=row.ticker.encode(),
                value=report.SerializeToString()
            )

        producer.flush()


if __name__ == "__main__":
    main()
