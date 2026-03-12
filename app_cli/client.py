import argparse
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.csv as pv
import zipfile
import io
import cache
import threading
import requests

def worker(start, stop, table, results, hit_stats):

    session = requests.Session()

    state_col = table.column("state_code")
    tract_col = table.column("census_tract")
    income_col = table.column("income")

    state_counts = {} # state -> [under_count, total_count]
    hits = 0
    lookups = 0

    for i in range(start, stop):

        try:
            state = state_col[i].as_py()
            tract = tract_col[i].as_py()
            income = income_col[i].as_py()

            # Skip bad rows (invalid tract or income)
            if not tract or not tract.isdigit() or income is None or income <= 0:
                continue

            # Lookup tract median income via REST server
            url = f"http://server:8001/{tract}"
            median, hit = cache.http_get(url, session)

            lookups += 1
            if hit:
                hits += 1

            # Skip if server returned 404
            if median is None:
                continue

            median = float(median)

            # Initialize state counter if needed
            if state not in state_counts:
                state_counts[state] = [0, 0]

            # Count under median incomes
            if income < median:
                state_counts[state][0] += 1

            # Count total rows for state
            state_counts[state][1] += 1

        except:
            # Skip malformed rows safely
            continue

    # Save thread results for aggregation later
    results.append(state_counts)
    hit_stats.append((hits, lookups))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file_path")
    parser.add_argument("--rows", type=int, default=-1)
    parser.add_argument("--cache", type=int, default=1000)
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()

    file_path = args.file_path
    rows = args.rows
    cache_size = args.cache
    num_threads = args.threads

    #print("reading data")
    if file_path.endswith(".parquet"):
        #print("reading parquet")
        table = pq.read_table(file_path, columns=["state_code", "census_tract", "income"])
    else:
        #print("reading zip")
        with zipfile.ZipFile(file_path) as z:
            csv_name = z.namelist()[0]
            with z.open(csv_name) as f:
                convert = pv.ConvertOptions(include_columns=["state_code", "census_tract", "income"], column_types={"state_code": pa.string(), "census_tract": pa.string(), "income": pa.float64()})
                table = pv.read_csv(f, convert_options=convert)

    if rows != -1:
        table = table.slice(0, rows)

    # Initialize cache
    #print("initialize cache")
    cache.init_cache(cache_size)

    total_rows = table.num_rows
    threads = []
    results = []
    hit_stats = []

    # Split rows evenly across threads
    #print("start threads")
    chunk = total_rows // num_threads
    for t in range(num_threads):
        start = t * chunk
        stop = total_rows if t == num_threads - 1 else (t + 1) * chunk
        thread = threading.Thread(target=worker, args=(start, stop, table, results, hit_stats))
        threads.append(thread)
        thread.start()

    # Wait for threads to finish
    for thread in threads:
        thread.join()
    #print("finished threads")

    # Compute partial stats/counts for each thread, and wait until after all threads return (using join) before adding to get totals
    state_totals = {}
    total_hits = 0
    total_lookups = 0

    for r in results:
        for state, (under, total) in r.items():
            if state not in state_totals:
                state_totals[state] = [0, 0]
            state_totals[state][0] += under
            state_totals[state][1] += total

    for h, l in hit_stats:
        total_hits += h
        total_lookups += l

    # Print results per state
    for state in sorted(state_totals):
        under, total = state_totals[state]
        pct = int((under * 100) // total)
        print(f"{state}: {pct}% of {total}")

    # Print overall cache hit rate
    hit_rate = int((total_hits * 100) // total_lookups)
    print(f"hit rate: {hit_rate}%")

if __name__ == "__main__":
    main()
