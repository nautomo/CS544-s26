"""
Test coverage:

Covered endpoints:
- POST /<db>/api/companies/<ticker>
- POST /<db>/api/companies/<ticker>/records/<date>
- GET /<db>/api/companies/<ticker>/records
- GET /<db>/api/companies/<ticker>/records/<date>
- GET /<db>/api/companies/<ticker>/records/range
- GET /<db>/api/companies/<ticker>/records/monthly
"""
import requests
import random
import string

BASE = "http://localhost:5000/test/api"

def random_ticker():
    return "".join(random.choices(string.ascii_uppercase, k=8))

def test_add_and_get_company():
    # use random tickers so tests don't interfere with data from previous runs
    ticker = random_ticker()

    # Create a company
    r = requests.post(f"{BASE}/companies/{ticker}",
                      json={"name": "MegaCorp", "sector": "Everything"})
    assert r.status_code == 201
    data = r.json()
    assert data["ticker"] == ticker
    assert data["name"] == "MegaCorp"
    assert data["sector"] == "Everything"

    # Update the same company (upsert)
    r = requests.post(f"{BASE}/companies/{ticker}",
                      json={"name": "Mega Corp", "sector": "All The Things"})
    assert r.status_code == 201
    data = r.json()
    assert data["ticker"] == ticker
    assert data["name"] == "Mega Corp"
    assert data["sector"] == "All The Things"


def test_add_stock_records():
    # use random tickers so tests don't interfere with data from previous runs
    ticker = random_ticker()

    # Create a company first
    r = requests.post(f"{BASE}/companies/{ticker}",
                      json={"name": "TestCo", "sector": "Testing"})
    assert r.status_code == 201

    # Add a stock record for date 1
    date1 = "2023-01-01"
    r = requests.post(f"{BASE}/companies/{ticker}/records/{date1}",
                      json={"high": 100, "low": 90})
    assert r.status_code == 201
    data = r.json()
    assert data["ticker"] == ticker
    assert data["date"] == date1

    # Add a stock record for date 2
    date2 = "2023-01-02"
    r = requests.post(f"{BASE}/companies/{ticker}/records/{date2}",
                      json={"high": 110, "low": 105})
    assert r.status_code == 201
    data = r.json()
    assert data["ticker"] == ticker
    assert data["date"] == date2

    # Update the record for date 2 (upsert)
    r = requests.post(f"{BASE}/companies/{ticker}/records/{date2}",
                      json={"high": 115, "low": 108})
    assert r.status_code == 201
    data = r.json()
    assert data["ticker"] == ticker
    assert data["date"] == date2


def test_get_all_stock_records():
    # use random tickers so tests don't interfere with data from previous runs
    ticker = random_ticker()
    company_name = "Multi-Record Inc."
    company_sector = "Data"

    # Create a company first
    r = requests.post(f"{BASE}/companies/{ticker}",
                      json={"name": company_name, "sector": company_sector})
    assert r.status_code == 201

    # Stock records to be inserted, ordered by date
    records = [
        {"date": "2023-02-01", "high": 200, "low": 190},
        {"date": "2023-02-02", "high": 210, "low": 205},
        {"date": "2023-02-03", "high": 208, "low": 198},
    ]

    # Insert the stock records
    for record in records:
        r = requests.post(f"{BASE}/companies/{ticker}/records/{record['date']}",
                          json={"high": record['high'], "low": record['low']})
        assert r.status_code == 201

    # Get all records for the ticker
    r = requests.get(f"{BASE}/companies/{ticker}/records")
    assert r.status_code == 200

    data = r.json()
    assert len(data) == len(records)

    # The API returns records sorted by date, so we can compare them directly
    for i, returned_record in enumerate(data):
        expected_record = records[i]
        assert returned_record["ticker"] == ticker
        assert returned_record["name"] == company_name
        assert returned_record["sector"] == company_sector
        assert returned_record["date"] == expected_record["date"]
        assert returned_record["high"] == expected_record["high"]
        assert returned_record["low"] == expected_record["low"]


def test_get_stock_records_monthly():
    # use random tickers so tests don't interfere with data from previous runs
    ticker = random_ticker()
    company_name = "Monthly Averages Inc."
    company_sector = "Analytics"

    # Create a company first
    r = requests.post(f"{BASE}/companies/{ticker}",
                      json={"name": company_name, "sector": company_sector})
    assert r.status_code == 201

    # Stock records to be inserted, spanning multiple months
    all_records = [
        {"date": "2023-05-10", "high": 500, "low": 490},
        {"date": "2023-05-20", "high": 510, "low": 505},
        {"date": "2023-06-15", "high": 520, "low": 515},
        {"date": "2023-06-25", "high": 530, "low": 525},
        {"date": "2023-07-05", "high": 540, "low": 535},
    ]

    # Insert the stock records
    for record in all_records:
        r = requests.post(f"{BASE}/companies/{ticker}/records/{record['date']}",
                          json={"high": record['high'], "low": record['low']})
        assert r.status_code == 201

    # Manually compute expected monthly averages
    expected_averages = {
        "2023-05": round((500 + 510) / 2, 4),
        "2023-06": round((520 + 530) / 2, 4),
        "2023-07": round(540 / 1, 4),
    }

    # Get monthly average records for the ticker
    r = requests.get(f"{BASE}/companies/{ticker}/records/monthly")
    assert r.status_code == 200

    data = r.json()
    assert len(data) == len(expected_averages)

    # The API returns records sorted by month, so we can check them
    returned_averages = {item['month']: item['avg_high'] for item in data}
    assert returned_averages == expected_averages


def test_get_stock_record_by_date():
    # use random tickers so tests don't interfere with data from previous runs
    ticker = random_ticker()
    company_name = "Specific Date Inc."
    company_sector = "Time"

    # Create a company first
    r = requests.post(f"{BASE}/companies/{ticker}",
                      json={"name": company_name, "sector": company_sector})
    assert r.status_code == 201

    # Stock records to be inserted
    record1 = {"date": "2023-03-01", "high": 300, "low": 290}
    record2 = {"date": "2023-03-02", "high": 310, "low": 305}

    # Insert the stock records
    r = requests.post(f"{BASE}/companies/{ticker}/records/{record1['date']}",
                      json={"high": record1['high'], "low": record1['low']})
    assert r.status_code == 201
    r = requests.post(f"{BASE}/companies/{ticker}/records/{record2['date']}",
                      json={"high": record2['high'], "low": record2['low']})
    assert r.status_code == 201

    # Get a single record by date
    r = requests.get(f"{BASE}/companies/{ticker}/records/{record1['date']}")
    assert r.status_code == 200

    data = r.json()

    # Assert the returned record is the correct one
    assert data["ticker"] == ticker
    assert data["name"] == company_name
    assert data["sector"] == company_sector
    assert data["date"] == record1["date"]
    assert data["high"] == record1["high"]
    assert data["low"] == record1["low"]


def test_get_stock_records_by_range():
    # use random tickers so tests don't interfere with data from previous runs
    ticker = random_ticker()
    company_name = "Date Range Corp."
    company_sector = "Time Travel"

    # Create a company first
    r = requests.post(f"{BASE}/companies/{ticker}",
                      json={"name": company_name, "sector": company_sector})
    assert r.status_code == 201

    # Stock records to be inserted
    all_records = [
        {"date": "2023-04-01", "high": 400, "low": 390},  # Outside range
        {"date": "2023-04-02", "high": 410, "low": 405},  # Start of range
        {"date": "2023-04-03", "high": 420, "low": 415},  # Inside range
        {"date": "2023-04-04", "high": 418, "low": 412},  # End of range
        {"date": "2023-04-05", "high": 430, "low": 425},  # Outside range
    ]

    # Insert the stock records
    for record in all_records:
        r = requests.post(f"{BASE}/companies/{ticker}/records/{record['date']}",
                          json={"high": record['high'], "low": record['low']})
        assert r.status_code == 201

    # Define the range for the query
    start_date = "2023-04-02"
    end_date = "2023-04-04"

    # Get records within the date range
    r = requests.get(f"{BASE}/companies/{ticker}/records/range",
                     params={"start": start_date, "end": end_date})
    assert r.status_code == 200

    data = r.json()

    # Records expected to be in the response
    expected_records_in_range = [rec for rec in all_records if start_date <= rec['date'] <= end_date]

    assert len(data) == len(expected_records_in_range)

    # The API returns records sorted by date, so we can compare them directly
    for i, returned_record in enumerate(data):
        expected_record = expected_records_in_range[i]
        assert returned_record["ticker"] == ticker
        assert returned_record["name"] == company_name
        assert returned_record["sector"] == company_sector
        assert returned_record["date"] == expected_record["date"]
        assert returned_record["high"] == expected_record["high"]
        assert returned_record["low"] == expected_record["low"]
