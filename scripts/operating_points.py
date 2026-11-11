# OPERATING POINTS
# Compares every pair of segments from the three classes that are not repeats. protocol.md fixes the rules.
# Writes operating_point_pairs.csv. Read it with report.py.

import pandas as pd
from src import config
from src.data_io import load, save_result
from src.segment_map import LOW_VOLTAGE, SEGMENTS

POINT = ["rpm", "map", "tps"]            # the columns that define an operating point

names = config.FAULT_NAMES
df = load()
other_columns = [column for column in df.columns if column not in POINT + ["fault"]]

# Low-voltage segments repeat lean ones, so they are left out
segments = [segment for segment in SEGMENTS if segment[0] != LOW_VOLTAGE]

# Mean and SD of every column inside each segment
mean_of, sd_of = {}, {}
for label, number, first, last, fold in segments:
    rows = df.iloc[first:last + 1].drop(columns="fault")
    mean_of[(label, number)] = rows.mean()
    sd_of[(label, number)] = rows.std()

# One row per pair of segments. A gap is the difference in means over the average of the two SDs
pairs = []
for position, (label_a, number_a, first_a, last_a, fold_a) in enumerate(segments):
    for label_b, number_b, first_b, last_b, fold_b in segments[position + 1:]:
        a, b = (label_a, number_a), (label_b, number_b)
        gap = (mean_of[a] - mean_of[b]).abs() / ((sd_of[a] + sd_of[b]) / 2)
        pair = {"class a": names[label_a], "segment a": number_a, "fold a": fold_a,
                "class b": names[label_b], "segment b": number_b, "fold b": fold_b,
                "distance": gap[POINT].max()}       # the largest gap on the operating-point columns
        pair.update({f"gap: {column}": gap[column] for column in POINT + other_columns})
        pairs.append(pair)

print(f"{len(segments)} segments, {len(pairs)} pairs")
save_result(pd.DataFrame(pairs), "operating_point_pairs.csv")
print("now run report.py")
