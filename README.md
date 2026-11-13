# EGEC 499: From Data to Device

**Student:** Luis Rey Salinas Jr.
**Mentor:** Dr. Yoonsuk Choi
**School:** California State University, Fullerton
**Department:** Electrical Engineering

Which engine faults stay detectable using only measurements an OBD-II port can supply,
how much detection performance is lost as the measurements are restricted, and do real cars supply what is left?

Fall 2026 is the analysis on an existing dataset. Spring 2027 is the physical build with an ESP32-based reader, and a survey of what real cars report.

## Data

EngineFaultDB (Vergara et al., IEEE Access 11, 2023, DOI 10.1109/ACCESS.2023.3331316, GPL-3.0) at https://github.com/leoxthomas/EngineFaultDB.
The CSV is not committed. The startup cell downloads it into `data/raw/`, and `data/DATA_SOURCE.md` pins the exact file by checksum.

**One block of this dataset repeats another.** Read `duplication.md` before using any four-class result from this repository.

## Files

| document | what it holds |
| --- | --- |
| `protocol.md` | the evaluation rules, and how each one came out |
| `duplication.md` | the duplication finding and how to check it |
| `dataset_inventory.md` | what two public road datasets record, against what this project needs |
| `data/DATA_SOURCE.md` | the dataset's URL, retrieval date and checksum |

| module in `src/` | what it holds |
| --- | --- |
| `config.py` | paths, column names, fault names |
| `data_io.py` | loading the data, saving and loading results |
| `audit.py` | the availability tier of each column, and the restriction ladder |
| `splitting.py` | the blocked split and its checks |
| `segment_map.py` | the 56 segments and the fold each one is tested in |

## Running it

Everything runs in Google Colab with pandas, numpy, scipy, scikit-learn and matplotlib.
Paste `colab/startup_cell.py` as the first cell, with the details at its top filled in. Run the scripts below in order, then paste `colab/finish_cell.py` as the last cell.

| step | script | what it does | writes |
| --- | --- | --- | --- |
| 1 | `scripts/week1_verify.py` | checks the dataset's structure | `week1_lag1.csv`, `week1_structure.json` |
| 2 | `scripts/label_map.py` | confirms which label is which fault | `label_evidence.csv` |
| 3 | `scripts/folds.py` | checks the blocked split | `fold_drift.csv` |
| 4 | `scripts/ladder.py` | the restriction ladder on blocked folds | `ladder.csv`, `ladder_folds.csv` |
| 5 | `scripts/diagnostics.py` | four checks on the port-only rung | four `port_*.csv` files and two others |
| 6 | `scripts/segments.py` | finds the segments inside each block | five `segment_*.csv` files |
| 7 | `scripts/segment_ladder.py` | the ladder again, with whole segments held out | `segment_ladder.csv`, `segment_ladder_folds.csv` |
| 8 | `scripts/operating_points.py` | compares every pair of segments | `operating_point_pairs.csv` |
| 9 | `scripts/report.py` | prints every table and draws every figure from the saved results | the four figures |

Two scripts stand alone, need only pandas and numpy, and can be run at any time:
`scripts/duplication_check.py` reproduces `duplication.md`, and `scripts/dataset_inventory.py` reproduces `dataset_inventory.md`.

- **Restart the runtime after editing anything in `src/`.** Python keeps the imported copy for the rest of the session.
- **Results are written to Google Drive**, and the finish cell copies them into `results/` and `figures/`. To run outside Colab, change `DRIVE` in `src/config.py`.
- **Every result CSV carries a `run_at` column**, and every script that reads one prints it first, so stale results are visible.

## Methods

The rules are in `protocol.md`. In short:

- **The file is ordered.** Each class is a block of 1000-row segments, and each segment holds one operating point. A shuffled split puts rows from one segment on both sides, so it tests conditions the model has already seen.
- **Blocked split:** each class block is cut into five contiguous pieces, and the rows within 500 of a test piece are dropped from training.
- **Segment split:** whole segments are held out in 11 folds, with each low-voltage segment kept in the fold of the lean segment it repeats.
- **The ladder:** five nested sets of columns, from all fourteen down to the four dedicated PIDs. `audit.py` checks the nesting on import.
- **Scoring:** macro F1, reported as the range across folds. Random guessing scores 0.249. A paired *t*-test on the matched folds is supporting evidence, not proof.

## Findings so far

As of 12 November 2026. Each item names the file it comes from.

### The dataset

- **Each class block is a run of 1000-row segments.** 154 of the 168 largest row-to-row steps fall exactly on a segment boundary (`segment_edges.csv`).
- **The low-voltage block repeats the lean-mixture block.** Its MAP and TPS columns are identical to lean's across 14,000 rows, offset by one segment, and the other twelve columns match segment for segment (`duplication.md`).
- **So the file holds 42 distinct operating points, not 56.** The 14 low-voltage segments are the repeats.
- **Fault is confounded with operating point.** Of the 581 pairs of segments from different classes, 3 sit at a matched operating point and 10 at a matched or loosely matched one. 27 of the 42 segments have no such partner (`operating_point_pairs.csv`). A score above chance can therefore come from recognizing operating points, not faults.
- **At the few shared operating points, the columns that separate classes are analyzer gases and lambda.** HC separates no fault from rich mixture, and lambda, CO and CO2 separate rich from lean. Each verdict rests on one to four pairs, so this is a description and not a test.
- **MAP and TPS are recorded in volts**, not the kPa and percent the paper states: 0.45 to 4.55 and 0.38 to 4.05 (`week1_structure.json`).
- **Several columns overlap with others.** AFR is 14.7 times lambda. Consumption per 100 km follows from fuel rate and speed. Engine speed and road speed correlate at 0.997 because the whole file was recorded in one gear. MAP and TPS correlate at 0.884.
- **High lag-1 correlation comes from the segment structure.** Across a block it is above 0.99 for eleven of the fourteen columns; inside a segment it is near zero for twelve (`week1_lag1.csv`, `segment_lag1.csv`).

### The models

**Leakage is worth 0.42 macro F1.** With all fourteen columns the random forest averages 0.755 under a shuffled split and 0.334 under the blocked split (`ladder.csv`).

**The ladder, four classes.** Each cell is the range across folds with the mean in brackets: five blocked folds (`ladder.csv`) and eleven segment folds (`segment_ladder.csv`).

| rung | columns | random forest, blocked | random forest, segment | logistic regression, blocked | logistic regression, segment |
| --- | --- | --- | --- | --- | --- |
| all 14 | 14 | 0.127 to 0.583 (0.334) | 0.100 to 0.446 (0.300) | 0.259 to 0.440 (0.354) | 0.160 to 0.526 (0.347) |
| no dynamometer | 12 | 0.151 to 0.499 (0.302) | 0.100 to 0.394 (0.318) | 0.237 to 0.475 (0.354) | 0.108 to 0.638 (0.338) |
| no analyzer gases | 8 | 0.200 to 0.497 (0.294) | 0.053 to 0.372 (0.281) | 0.146 to 0.347 (0.218) | 0.039 to 0.446 (0.192) |
| no wideband lambda | 6 | 0.160 to 0.437 (0.282) | 0.011 to 0.424 (0.261) | 0.082 to 0.225 (0.176) | 0.000 to 0.417 (0.166) |
| dedicated PIDs only | 4 | 0.188 to 0.435 (0.321) | 0.009 to 0.589 (0.275) | 0.075 to 0.176 (0.143) | 0.000 to 0.425 (0.132) |

- **The two designs agree.** Their means are within 0.05 at every rung. They split the same file, so this is not independent confirmation.
- **Random forest: no rung can be told apart from another.** All fourteen columns against the four PIDs is +0.013 on the blocked folds (*p* = 0.846) and +0.025 on the segment folds (*p* = 0.616). No cost of restriction has been established.
- **Logistic regression falls, mostly when the analyzer gases are removed.** All fourteen against the four PIDs is +0.211 (*p* = 0.005) and +0.215 (*p* = 0.002). On the segment folds its top and bottom ranges overlap, and the tests are uncorrected.
- **On the segment folds, every rung's fold range covers random guessing**, including all fourteen columns. So "no cost established" means the ladder had little to lose. It does not show that the port columns match the laboratory set.
- **With low voltage left out, the reading is the same.** Random guessing is 0.331 there. Random forest drops +0.070 from top to bottom (*p* = 0.151) and logistic regression +0.301 (*p* = 0.002) (`segment_ladder.csv`).
- **The lean and low-voltage confusion is the duplication, not a detection limit.** 44% of true low voltage is predicted as lean mixture (`port_confusion.csv`), because the two classes carry the same values. **It must not be reported as a limit of the OBD-II port.**

### Real cars

- **Two public road datasets record all four dedicated PIDs**, and one records fuel trim. Neither has fault labels, lambda or control module voltage (`dataset_inventory.md`).

## Earlier claims that no longer stand

| earlier claim | what replaced it |
| --- | --- |
| Consecutive rows are near copies of one another | Inside a segment, lag-1 is near zero for twelve of the fourteen columns |
| Engine speed is worth about 116 independent rows | 42 distinct operating points. The 116 is still in `week1_structure.json` and should not be cited |
| Engine speed and road speed are one quantity recorded twice | They are tied by the single gear used |
| Low voltage leaves more unburnt fuel than lean | It reverses on the 14,000 matched rows. The check was removed from `label_map.py` |
| The file holds 57 segments | 56, of which 42 are distinct |
| Restricting to the four PIDs costs almost nothing | No cost has been established; the rungs cannot be told apart |
