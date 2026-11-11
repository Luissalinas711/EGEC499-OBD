# Duplication in EngineFaultDB

**Luis Salinas · EGEC 499 · 10 November 2026**

In EngineFaultDB, the low-voltage block repeats the lean-mixture block.
Its MAP and TPS columns are identical to lean's across 14,000 rows, and its other twelve columns match lean's segment by segment.
This note records what the file contains and how to check it. It does not interpret the cause.

**The file.** `EngineFaultDB_Final.csv`, 5,334,236 bytes, 55,999 rows, 15 columns, downloaded from `raw.githubusercontent.com/leoxthomas/EngineFaultDB`.
SHA-256 `70021a35b2b2efb294e49f4c78b80a391a05414d44d4564c429645eb32260763`.

The sections below are numbered to match the output of `scripts/duplication_check.py`.

## 1. Block boundaries

The label column changes three times, so each class is one unbroken run of rows. Row numbers count from 0.

| Label | Class | Rows | Count | Full 1000-row segments |
|---|---|---|---|---|
| 0 | no fault | 0 – 15,999 | 16,000 | 16 |
| 1 | rich mixture | 16,000 – 26,997 | 10,998 | 10 |
| 2 | lean mixture | 26,998 – 41,997 | 15,000 | 15 |
| 3 | low voltage | 41,998 – 55,998 | 14,001 | 14 |

## 2. Row-by-row comparison

Low-voltage rows **41,998 – 55,997** were compared with lean-mixture rows **27,998 – 41,997**, 14,000 rows in all.
Counting from the start of each block, low-voltage row *n* is compared with lean row *n* + 1000.

**MAP and TPS are identical in every one of the 14,000 rows.**
The largest absolute difference is 0.0000000000 in both, and `numpy.array_equal` returns `True` for each.
The other twelve columns are not identical row by row: their largest differences run from 0.109 (O2) to 429.322 (RPM).

## 3. Segment means, the other twelve columns

The 14,000 rows form fourteen pairs of 1000-row segments.
For each pair and each column, the gap is the difference between the two segment means, divided by the average of the two segments' standard deviations.
The table gives the median and the largest of the fourteen gaps.

| Column | Median | Worst |
|---|---|---|
| Force | 0.0341 | 0.0813 |
| Power | 0.0251 | 0.0641 |
| RPM | 0.0393 | 0.1242 |
| Consumption L/H | 0.0405 | 0.0912 |
| Consumption L/100KM | 0.0247 | 0.1156 |
| Speed | 0.0332 | 0.0937 |
| CO | 0.0326 | 0.0835 |
| HC | 0.0279 | 0.1076 |
| CO2 | 0.0235 | 0.0786 |
| O2 | 0.0235 | 0.1325 |
| Lambda | 0.0214 | 0.1213 |
| AFR | 0.0216 | 0.1220 |

The largest gap in the table is 0.1325 of a standard deviation (O2).

## 4. Repeated segments

Every candidate 1000-row segment in the file was compared on MAP and TPS.
Candidates were taken on two grids per block, one counted from the block's first row and one from its last, because two blocks are not a whole number of segments long.
That gives 79 candidates and 65 distinct traces, 14 of which appear twice.
All 14 are the pairs above: lean segments 2 to 15 with low-voltage segments 1 to 14, in order.
No other candidate repeats.

## 5. The same gap between every pair of classes

For scale, the same gap was computed between classes.
For each segment it is the largest gap across the fourteen columns to the nearest segment of the other class.

| Pair | Median | Closest |
|---|---|---|
| no fault / rich mixture | 15.35 | 5.78 |
| no fault / lean mixture | 37.02 | 8.61 |
| no fault / low voltage | 37.14 | 8.49 |
| rich mixture / lean mixture | 15.34 | 7.81 |
| rich mixture / low voltage | 15.51 | 7.90 |
| **lean mixture / low voltage** | **0.09** | **0.04** |

## How to check

Put the CSV in the folder the script is run from, or in `data/raw/` below it, and run `scripts/duplication_check.py`.
The script needs only pandas and numpy and imports nothing else from this repository.
It compares the file's SHA-256 with the value above, finds the block boundaries from the label column, and prints the figures in sections 1 to 5.
Run on 10 November 2026: its output matched this note.
