import matplotlib.pyplot as plt
import csv

formats = []
times = []

with open("storage_times.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        formats.append(row["format"])
        times.append(float(row["time_seconds"]))

plt.bar(formats, times)
plt.ylabel("Seconds")
plt.title("Storage Format Load Time")
plt.savefig("storage.svg")
