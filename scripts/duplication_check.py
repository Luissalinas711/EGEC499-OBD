# DUPLICATION CHECK
# Compares the low voltage block of EngineFaultDB with the lean mixture block.
# Needs only pandas and numpy. Nothing is imported from src/.

import hashlib
import os

import numpy as np
import pandas as pd

RECORDED_SHA256 = "70021a35b2b2efb294e49f4c78b80a391a05414d44d4564c429645eb32260763"

# The first path that exists is used
CSV_PATHS = [
    "EngineFaultDB_Final.csv",
    "data/raw/EngineFaultDB_Final.csv",
    "/content/egec499-obd/data/raw/EngineFaultDB_Final.csv",
]

NAMES = {0: "no fault", 1: "rich mixture", 2: "lean mixture", 3: "low voltage"}
LEAN = 2
LOW_VOLTAGE = 3
SEGMENT = 1000                  # rows in one segment
SHIFT = 1000                    # low voltage row n is compared with lean mixture row n + SHIFT
FINGERPRINT = ["MAP", "TPS"]    # columns a segment is matched on in step 4
PAIRS = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]    # class pairs in step 5


def class_blocks(labels):
    # {label: (first_row, last_row)} for each unbroken run of one label
    starts = [0] + [row for row in range(1, len(labels)) if labels[row] != labels[row - 1]]
    ends = [start - 1 for start in starts[1:]] + [len(labels) - 1]
    return {int(labels[start]): (start, end) for start, end in zip(starts, ends)}


def segment_stats(rows):
    # Mean and SD of every column in each full segment, counted from the first row given
    full = rows.iloc[:len(rows) // SEGMENT * SEGMENT]
    number = np.arange(len(full)) // SEGMENT
    return full.groupby(number).mean(), full.groupby(number).std()


def gap(mean_a, sd_a, mean_b, sd_b):
    # Difference in means divided by the average of the two SDs, per column
    return (mean_a - mean_b).abs() / ((sd_a + sd_b) / 2)


# LOAD
found = [path for path in CSV_PATHS if os.path.isfile(path)]
if not found:
    raise SystemExit("dataset not found. Looked in:\n   " + "\n   ".join(CSV_PATHS))
path = found[0]

with open(path, "rb") as file:
    sha256 = hashlib.sha256(file.read()).hexdigest()

data = pd.read_csv(path)
measurements = [name for name in data.columns if name != "Fault"]
blocks = class_blocks(data["Fault"].to_numpy())

print(f"\n{os.path.abspath(path)}")
print(f"{os.path.getsize(path):,} bytes, {len(data):,} rows, {len(data.columns)} columns")
print(f"SHA-256 {sha256}")
print("matches the recorded checksum" if sha256 == RECORDED_SHA256 else "DIFFERS from the recorded checksum")

# 1. Where each class starts and ends
print("\n1. BLOCK BOUNDARIES")
for label, (first, last) in blocks.items():
    rows = last - first + 1
    print(f"   label {label}  {NAMES[label]:<13} rows {first:>6,} to {last:>6,}"
          f"   {rows:>6,} rows   {rows // SEGMENT} full segments")

# 2. The two row ranges, column by column
lean_first, lean_last = blocks[LEAN]
low_first, low_last = blocks[LOW_VOLTAGE]
rows = min(low_last - low_first + 1, lean_last - lean_first + 1 - SHIFT) // SEGMENT * SEGMENT

low = data[measurements].iloc[low_first:low_first + rows].reset_index(drop=True)
lean = data[measurements].iloc[lean_first + SHIFT:lean_first + SHIFT + rows].reset_index(drop=True)

print("\n2. ROW-BY-ROW COMPARISON")
print(f"   low voltage rows {low_first:,} to {low_first + rows - 1:,}   against"
      f"   lean mixture rows {lean_first + SHIFT:,} to {lean_first + SHIFT + rows - 1:,}")
print(f"   {rows:,} rows compared\n")
print(f"   {'column':<22}{'identical':>10}{'largest difference':>22}")

other_columns = []
for column in measurements:
    identical = np.array_equal(low[column], lean[column])
    largest = (low[column] - lean[column]).abs().max()
    print(f"   {column:<22}{'yes' if identical else 'no':>10}{largest:>22.10f}")
    if not identical:
        other_columns.append(column)

# 3. The columns that are not identical, segment by segment
low_mean, low_sd = segment_stats(low[other_columns])
lean_mean, lean_sd = segment_stats(lean[other_columns])
gaps = gap(low_mean, low_sd, lean_mean, lean_sd)    # one row per paired segment

print("\n3. SEGMENT MEANS, THE COLUMNS THAT ARE NOT IDENTICAL")
print(f"   difference in means / within-segment SD, over {len(gaps)} paired segments\n")
print(f"   {'column':<22}{'median':>10}{'worst':>10}")
for column in other_columns:
    print(f"   {column:<22}{gaps[column].median():>10.4f}{gaps[column].max():>10.4f}")

# 4. Every candidate segment in the file, matched on the fingerprint columns
# The grid is taken from both ends of a block, since a block can hold a partial segment
seen = {}
for label, (first, last) in blocks.items():
    count = (last - first + 1) // SEGMENT
    from_start = [first + i * SEGMENT for i in range(count)]
    from_end = [last + 1 - (i + 1) * SEGMENT for i in range(count)]
    for start in sorted(set(from_start + from_end)):
        trace = data[FINGERPRINT].iloc[start:start + SEGMENT].to_numpy().tobytes()
        number = (start - first) // SEGMENT + 1
        seen.setdefault(trace, []).append(f"{NAMES[label]} segment {number} at row {start:,}")

candidates = sum(len(group) for group in seen.values())
repeated = [group for group in seen.values() if len(group) > 1]

print("\n4. REPEATED SEGMENTS")
print(f"   {candidates} candidate segments matched on {', '.join(FINGERPRINT)}")
print(f"   {len(seen)} distinct, {len(repeated)} appear more than once")
for group in repeated:
    print(f"      {'  ==  '.join(group)}")

# 5. The same gap between every pair of classes
stats = {}
for label, (first, last) in blocks.items():
    stats[label] = segment_stats(data[measurements].iloc[first:last + 1])

print("\n5. NEAREST-SEGMENT DISTANCE, EVERY PAIR OF CLASSES")
print("   largest gap across columns, from each segment to the nearest segment of the other class\n")
print(f"   {'pair':<30}{'median':>10}{'closest':>10}")
for a, b in PAIRS:
    mean_a, sd_a = stats[a]
    mean_b, sd_b = stats[b]
    nearest = []
    for i in range(len(mean_a)):
        to_each = gap(mean_a.iloc[i], sd_a.iloc[i], mean_b, sd_b).max(axis=1)
        nearest.append(to_each.min())
    print(f"   {NAMES[a] + ' / ' + NAMES[b]:<30}{np.median(nearest):>10.2f}{min(nearest):>10.2f}")
print()
