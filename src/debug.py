from kafka import KafkaConsumer
import report_pb2

BROKER = "localhost:9092"
TOPIC = "stock_prices"


def main():
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BROKER,
        group_id="debug",
        auto_offset_reset="latest",
        enable_auto_commit=True
    )

    for msg in consumer:
        report = report_pb2.Report()
        report.ParseFromString(msg.value)

        print({
            "ticker": report.ticker,
            "date": report.date,
            "price": str(report.price),
            "partition": msg.partition
        })


if __name__ == "__main__":
    main()
