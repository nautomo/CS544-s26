import os, sys
import time
from flask import Flask, request, jsonify
from cassandra.cluster import Cluster
from cassandra.query import ConsistencyLevel

app = Flask(__name__)

project = os.environ.get("PROJECT", "p6")
nodes = [f"{project}-cassandra-1", f"{project}-cassandra-2", f"{project}-cassandra-3"]
session = None

# TODO: endpoints
# 1. Create/Update Company
@app.route("/<db>/api/companies/<ticker>", methods=["POST"])
def add_company(db, ticker):
    data = request.get_json()
    name = data.get("name")
    sector = data.get("sector")

    if not all([name, sector]):
        return jsonify({"error": "name and sector are required"}), 400

    session.execute(f"""
        INSERT INTO {db}.stocks (ticker, name, sector)
        VALUES (%s, %s, %s)
    """, (ticker, name, sector))

    return jsonify({"ticker": ticker, "name": name, "sector": sector}), 201


# 2. Add Stock Record
@app.route("/<db>/api/companies/<ticker>/records/<date>", methods=["POST"])
def add_stock(db, ticker, date):
    data = request.get_json()
    high = data.get("high")
    low = data.get("low")

    if any(v is None for v in [high, low]):
        return jsonify({"error": "high and low are required"}), 400

    session.execute(f"""
        INSERT INTO {db}.stocks (ticker, date, high, low)
        VALUES (%s, %s, %s, %s)
    """, (ticker, date, high, low))

    return jsonify({"ticker": ticker, "date": date}), 201


# 3. Get All Stock Records
@app.route("/<db>/api/companies/<ticker>/records", methods=["GET"])
def get_stocks(db, ticker):
    rows = session.execute(f"""
        SELECT ticker, date, high, low, name, sector
        FROM {db}.stocks
        WHERE ticker = %s
    """, (ticker,))

    valid_rows = [r for r in rows if r.date is not None]

    if not valid_rows:
        return jsonify({"error": "not found"}), 404

    result = []
    for r in valid_rows:
        result.append({
            "ticker": r.ticker,
            "name": r.name,
            "sector": r.sector,
            "date": str(r.date),
            "high": r.high,
            "low": r.low
        })

    return jsonify(result)


# 4. Get Specific Stock Record
@app.route("/<db>/api/companies/<ticker>/records/<date>", methods=["GET"])
def get_stock_date(db, ticker, date):
    rows = session.execute(f"""
        SELECT ticker, date, high, low, name, sector
        FROM {db}.stocks
        WHERE ticker = %s AND date = %s
    """, (ticker, date))

    for r in rows:
        if r.date:
            return jsonify({
                "ticker": r.ticker,
                "name": r.name,
                "sector": r.sector,
                "date": str(r.date),
                "high": r.high,
                "low": r.low
            })

    return jsonify({"error": "not found"}), 404


# 5. Get Stock Records in Range
@app.route("/<db>/api/companies/<ticker>/records/range", methods=["GET"])
def get_stock_range(db, ticker):
    start = request.args.get("start")
    end = request.args.get("end")

    if not start or not end:
        return jsonify({"error": "start and end query params are required"}), 400

    rows = session.execute(f"""
        SELECT ticker, date, high, low, name, sector
        FROM {db}.stocks
        WHERE ticker = %s AND date >= %s AND date <= %s
    """, (ticker, start, end))

    valid_rows = [r for r in rows if r.date is not None]

    if not valid_rows:
        return jsonify({"error": "not found"}), 404

    result = []
    for r in valid_rows:
        result.append({
            "ticker": r.ticker,
            "name": r.name,
            "sector": r.sector,
            "date": str(r.date),
            "high": r.high,
            "low": r.low
        })

    return jsonify(result)


# 6. Get Monthly Average
@app.route("/<db>/api/companies/<ticker>/records/monthly", methods=["GET"])
def get_stock_monthly(db, ticker):
    rows = session.execute(f"""
        SELECT date, high
        FROM {db}.stocks
        WHERE ticker = %s
    """, (ticker,))

    monthly = {}

    for r in rows:
        if r.date is None or r.high is None:
            continue

        try:
            month = str(r.date)[:7]
        except Exception:
            continue

        if month not in monthly:
            monthly[month] = []

        monthly[month].append(float(r.high))

    if not monthly:
        return jsonify({"error": "not found"}), 404

    result = []
    for m in sorted(monthly.keys()):
        avg = round(sum(monthly[m]) / len(monthly[m]), 4)
        result.append({
            "month": m,
            "avg_high": avg
        })

    return jsonify(result)

if __name__ == "__main__":
    for _ in range(30):
        try:
            cluster = Cluster(nodes)
            session = cluster.connect()
            break
        except Exception as ex:
            print(ex)
            time.sleep(2)
    else:
        print("Failed to connect to Cassandra after 30 attempts")
        sys.exit(1)

    # TODO: use session to create tables
    session.default_consistency_level = ConsistencyLevel.TWO

    for ks in ["prod", "test"]:
        session.execute(f"""
            CREATE KEYSPACE IF NOT EXISTS {ks}
            WITH replication = {{
                'class': 'SimpleStrategy',
                'replication_factor': 3
            }}
        """)

    for ks in ["prod", "test"]:
        session.execute(f"""
            CREATE TABLE IF NOT EXISTS {ks}.stocks (
                ticker TEXT,
                date DATE,
                high DOUBLE,
                low DOUBLE,
                name TEXT STATIC,
                sector TEXT STATIC,
                PRIMARY KEY ((ticker), date)
            ) WITH CLUSTERING ORDER BY (date ASC)
        """)

    app.run(host="0.0.0.0", port=5000, debug=True)
