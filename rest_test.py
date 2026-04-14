"""
Test coverage:

Covered endpoints:
- POST /<db>/api/companies/<ticker>
- POST /<db>/api/companies/<ticker>/records/<date>

Uncovered endpoints:
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
