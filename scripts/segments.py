# BLOCK SEGMENTS
# Part 1: the largest row-to-row steps in each column, within each block.
# Part 2: cut each block into fixed-length segments and record the mean of each.
# Part 3: for every pair of blocks, the distance between their segment means.
# Writes segment_edges.csv, segment_points.csv, segment_distance.csv

import numpy as np
import pandas as pd
from src import config
from src.data_io import class_runs, load, save_result

TOP = 3         # largest steps kept per column
SEGMENT = 1000  # cut length; check it against the part 1 output before reading part 2
WINDOW = 30     # positions profiled from the start of each segment in part 4
HELD = ["rpm", "map", "tps"]
names = config.FAULT_NAMES
df = load()
y = df["fault"].to_numpy()
columns = [column for column in df.columns if column != "fault"]
runs = class_runs(y)


# 1. LARGEST STEPS
# Each step is divided by its column's median step, so columns on different scales can be compared

rows = []
for start, end, label in runs:
    block = df.iloc[start:end]
    for column in columns:
        step = block[column].diff().abs().to_numpy()[1:]      # the first diff is NaN
        normal = np.median(step)
        for position in np.argsort(step, kind="stable")[-TOP:]:
            rows.append({"block": names[label], "column": column,
                         "row": start + int(position) + 1,     # absolute row in the file
                         "times_normal": float(step[position] / normal) if normal else np.nan})
edges = pd.DataFrame(rows)
save_result(edges, "segment_edges.csv")

# 2. SEGMENT MEANS
# Where the first cut falls is taken from part 1 rather than fixed
points, spans = [], []
for start, end, label in runs:
    found = edges.loc[edges["block"] == names[label], "row"] - start
    offset = int((found % SEGMENT).mode().iloc[0])
    cuts = sorted({0, end - start} |
                  {o for o in range(1, end - start) if o % SEGMENT == offset})
    for number, (a, b) in enumerate(zip(cuts[:-1], cuts[1:]), start=1):
        piece = df.iloc[start + a:start + b]
        spans.append((start + a, b - a))
        points.append({"block": names[label], "segment": number, "rows": b - a,
                       **{column: piece[column].mean() for column in HELD}})
segments = pd.DataFrame(points)
save_result(segments, "segment_points.csv")


# 3. DISTANCE BETWEEN BLOCKS
# For each segment of one block, the distance to the nearest segment of the other, 
# scaled by each column's spread and averaged. 
# Zero means identical segment means.

scale = df[HELD].std().to_numpy()
blocks = list(segments["block"].unique())
distance = pd.DataFrame(index=blocks, columns=blocks, dtype=float)
for first in blocks:
    for second in blocks:
        if first == second:
            continue
        a = segments.loc[segments["block"] == first, HELD].to_numpy() / scale
        b = segments.loc[segments["block"] == second, HELD].to_numpy() / scale
        distance.loc[first, second] = np.linalg.norm(a[:, None] - b[None, :],
                                                     axis=2).min(axis=1).mean()

distance.index.name = "block"
save_result(distance, "segment_distance.csv", index=True)


# 4. HOW EACH SEGMENT STARTS
# For every segment, how far each row sits from that segment's own median, by position from the segment's first row
# Averaged over segments and divided by the segment's own typical distance, so columns on different scales can be compared.

usable = [(at, length) for at, length in spans if length >= WINDOW]
profile = {}
for column in columns:
    values = df[column].to_numpy()
    rows = []
    for at, length in usable:
        piece = values[at:at + length]
        distance = np.abs(piece - np.median(piece))
        typical = np.median(distance)
        if typical:                          # a column that never moves has no scale
            rows.append(distance[:WINDOW] / typical)
    profile[column] = np.mean(rows, axis=0)

settling = pd.DataFrame(profile, index=pd.RangeIndex(WINDOW, name="position"))
print(f"{len(usable)} of {len(spans)} segments reach {WINDOW} rows")
save_result(settling, "segment_settling.csv", index=True)


# 5. HOW MUCH OF THE BLOCK-LEVEL CORRELATION IS THE SEGMENT STRUCTURE
# week1_lag1.csv measures lag-1 across a whole block. 
# Measured inside a single segment, the same figure says how much of it is row to row rather than the steps between segments.

within = []
for column in columns:
    values = df[column].to_numpy()
    scores = []
    for at, length in usable:
        piece = values[at:at + length]
        piece = piece - piece.mean()
        spread = np.sum(piece * piece)
        if spread:
            scores.append(np.sum(piece[:-1] * piece[1:]) / spread)
    within.append({"column": column, "within_segment": float(np.median(scores))})
save_result(pd.DataFrame(within), "segment_lag1.csv")
