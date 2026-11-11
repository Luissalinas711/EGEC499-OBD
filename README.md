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

The CSV is not committed. The startup cell downloads it into `data/raw/` the first time a session runs, and skips it afterwards;
the download URL is set at the top of `colab/startup_cell.py`.
The exact file every result here was computed from is pinned by checksum in `data/DATA_SOURCE.md`.

**One block of this dataset repeats another.** Read `duplication.md` before using any four-class result from this repository.

Needs pandas, numpy, scipy, scikit-learn and matplotlib. Everything runs in Google Colab with no extra installation.

## Layout

| path | kind | what it holds |
| --- | --- | --- |
| `README.md` | document | this file: what the project is, how to run it, what it has found |
| `protocol.md` | document | the evaluation rules, written before any result existed |
| `duplication.md` | document | the duplication finding, its row ranges, and how to check it |
| `data/DATA_SOURCE.md` | document | the dataset's URL, retrieval date and checksum |
| `src/config.py` | module | paths, column names, fault names |
| `src/data_io.py` | module | `load()`, `class_runs()`, and `save_result()` / `load_result()` |
| `src/audit.py` | module | the availability tier for each column, and the restriction ladder |
| `src/splitting.py` | module | `BlockedSplit`, `check_split`, `purge_width` |
| `src/segment_map.py` | module | the 56 segments and the fold each one is tested in |
| `scripts/week1_verify.py` | script | checks the flagged items against the plan |
| `scripts/label_map.py` | script | confirms which numeric label is which fault |
| `scripts/folds.py` | script | checks the splitter, measures operating-point drift |
| `scripts/ladder.py` | script | the restriction ladder, two models, three split designs |
| `scripts/diagnostics.py` | script | four checks on the port-only rung |
| `scripts/segments.py` | script | the segments inside each block, and what each one holds |
| `scripts/segment_ladder.py` | script | the ladder again, with whole segments held out |
| `scripts/duplication_check.py` | script | compares the low-voltage block with the lean-mixture block |
| `scripts/report.py` | script | rebuilds every table and figure from the committed results |
| `colab/startup_cell.py` | cell | mounts Drive, sets up git, clones the repo, fetches the data |
| `colab/finish_cell.py` | cell | copies results into the repo, commits and pushes |

Modules in `src/` are imported and print nothing on their own.
Scripts in `scripts/` are run directly.
The two files in `colab/` are pasted into the notebook rather than executed from the repository; fill in the details block at the top of `startup_cell.py` first.

`scripts/duplication_check.py` is the one script that stands alone.
It imports only pandas and numpy and checks the file's SHA-256 before it reports anything, so it can be run by someone who has the note but not this repository.

## Running it

Run `colab/startup_cell.py` as the first cell of the session, then each script below in order, then `colab/finish_cell.py` as the last cell.

| step | script | produces | needs |
| --- | --- | --- | --- |
| 1 | `scripts/week1_verify.py` | `week1_lag1.csv`, `week1_structure.json` | the CSV |
| 2 | `scripts/label_map.py` | `label_evidence.csv`, `label_evidence.png` | the CSV |
| 3 | `scripts/folds.py` | `fold_drift.csv` | step 1 |
| 4 | `scripts/ladder.py` | `ladder.csv`, `ladder_folds.csv` | step 1 |
| 5 | `scripts/diagnostics.py` | `port_rung_folds.csv`, `port_confusion.csv`, `port_importance.csv`, `port_subsets.csv`, `matched_separation.csv`, `within_recording_drift.csv` | step 1 |
| 6 | `scripts/segments.py` | `segment_edges.csv`, `segment_points.csv`, `segment_distance.csv`, `segment_settling.csv`, `segment_lag1.csv` | the CSV |
| 7 | `scripts/segment_ladder.py` | `segment_ladder.csv`, `segment_ladder_folds.csv` | the CSV |
| 8 | `scripts/report.py` | every table, and all four figures | steps 1 to 7 |

`scripts/duplication_check.py` is not in that order and nothing depends on it.
It reads the CSV, prints its own report and writes no files, so it can be run at any time.

The producing scripts save and check; none of them print a table or draw a figure.
`report.py` does all of that, from the committed results, and deletes the figures folder first so a leftover file cannot be mistaken for a current one.

Steps 2, 3 and 6 are quick to run. Steps 4 and 7 are the slow ones, which is why each writes a CSV.
Reporting is a separate script so that the figure and the tables can be changed and re-run.

These paths are Colab's. `src/config.py` writes results to `/content/drive/MyDrive/`, so running anywhere else means changing `DRIVE` there first.

## Editing it

Scripts in `scripts/` are read fresh every time they run, so editing one takes effect immediately.
The five modules in `src/` are not.
Once `config.py`, `data_io.py`, `splitting.py`, `audit.py` or `segment_map.py` has been imported, Python keeps that copy for the rest of the session,
and editing the file on disk changes nothing until the runtime is restarted. **Restart the runtime after editing anything in `src/`.**

Each script says what it is working from before it does any work:
`ladder.py` prints the rung names, and anything reading a result prints the date written inside that file.
If those lines disagree with the change you just made, the runtime is holding an old copy.

## Where results live

Results and figures are written to Google Drive, not into the repository.
A Colab restart empties `/content` and a fresh clone overwrites whatever it finds,
so a result written inside the repository can be deleted or quietly replaced by an older committed copy.
The finish cell copies Drive into `results/` and `figures/` when it pushes, so the repository still carries a record.

Every result CSV carries a `run_at` column written by the run that produced it, and every script that reads one prints that value first.
A file's own timestamp is reset by a clone, a copy or a Drive sync, so it cannot be trusted to say when the numbers were computed.

## Methods

The evaluation rules are in `protocol.md`, written before any restricted-feature result existed. In summary:

The file is ordered, not a shuffled sample.
Each class block is built from 1000-row segments, and each segment holds one operating point,
so rows inside a segment share both a fault and an operating condition.
A standard shuffled split puts rows from the same condition on both sides and tests the model on conditions it has already seen.

`BlockedSplit` cuts each class block into five contiguous pieces and tests piece *k* of every block in fold *k*,
so each fold holds all four classes and every test region is one continuous span of the file.
Rows beside a test piece are dropped from training; the width of that purge band is the half-life of the slowest column's block-level lag-1 correlation, 500 rows.
That correlation is produced by the steps between segments rather than by row-to-row smoothness, as `segment_lag1.csv` shows,
so what the band mainly removes is training rows that share a segment with the test piece.
Four properties are asserted before any score is used.

`audit.py` checks four things on import:
every rung names a real column, each rung nests inside the one above it, the widest rung is every audited column, and the narrowest rung is exactly the port tier.
The last one ties the ladder to the availability tiers, so a column cannot be reclassified without the ladder following.

A second design holds out whole segments instead of row spans.
`src/segment_map.py` lists the 56 segments and deals them into 11 folds, keeping each low-voltage segment in the fold of the lean segment it repeats.
`scripts/segment_ladder.py` runs the same ladder on those folds, with no purge band.
Its rules and its result are recorded in `protocol.md`.

Macro F1 is the primary metric, reported as the range across the folds and not as a single number.
Uniform random guessing over these four classes scores 0.249.
A difference between two rungs is also tested with a paired *t*-test on the five matched folds.
Five pairs is a small sample, so that test is supporting evidence and not proof.

## Findings so far

As of 11 November 2026. Each item names the file it comes from.

### The dataset

- **Each class block is a run of 1000-row segments, one operating point per segment.**
  154 of the 168 largest row-to-row steps fall exactly on a segment boundary, and the median boundary step is 59 times the typical step (`segment_edges.csv`).
  The paper describes acquisition by design of experiments, which is what these segments are.

- **The low-voltage block repeats the lean-mixture block.**
  Its MAP and TPS columns are identical to lean's, offset by one segment, across all 14,000 rows (file rows 41,998–55,997 against 27,998–41,997).
  The other twelve columns match segment for segment: their segment means differ by at most 0.1325 of a within-segment standard deviation.
  No other segment repeats anywhere in the file.
  The details are in `duplication.md`, and `scripts/duplication_check.py` reproduces them from the CSV alone.

- **So the file holds 42 distinct operating points, not 56.**
  `segment_points.csv` lists 57 segments, one of which is a single trailing row of the low-voltage block.
  Of the other 56, the 14 low-voltage segments are the repeats.

- **Fault is confounded with operating point.**
  Each class was recorded at its own operating points.
  On engine speed, MAP and TPS, a segment's nearest neighbor in another class is on average 0.41 to 0.65 whole-file standard deviations away, against 0.01 for lean and low voltage (`segment_distance.csv`).
  A score above chance can therefore come from recognizing operating points, not faults.

- **MAP and TPS are recorded in volts, not the kPa and percent the paper states.**
  They range from 0.45 to 4.55 and from 0.38 to 4.05 (`week1_structure.json`), the same ranges as the paper's Table 5.
  A throttle that never opened past 4.05 percent could not have produced the 33.95 kW the file records.

- **Several columns overlap with others.**
  AFR is 14.7 times lambda in every row, to within rounding.
  Consumption in L/100 km is 100 times fuel rate divided by road speed: on segment means the two agree at *r* = 0.999977.
  Engine speed and road speed correlate at 0.997 because the whole file was recorded in one gear, at 21.09 to 21.80 km/h per 1000 rpm in every segment. Inside a segment their correlation averages 0.06.
  MAP and TPS correlate at 0.884, so they share about four-fifths of their variance.

- **The high lag-1 correlations come from the segment structure, not from row-to-row smoothness.**
  Across a whole block, lag-1 is above 0.99 for eleven of the fourteen columns (`week1_lag1.csv`).
  Inside a segment it is near zero for twelve of the fourteen; MAP at 0.62 and TPS at 0.18 are the exceptions (`segment_lag1.csv`).

### The models

**Leakage is worth 0.42 macro F1.**
At all fourteen columns the random forest averages 0.755 under a shuffled split and 0.334 under the blocked split (`ladder.csv`).
Of that gap, 0.385 comes from breaking the block structure and 0.035 from rows next to the test piece.

**The restriction ladder, four classes, under both designs.**
Each cell is the range across the folds with their mean in brackets: five blocked folds (`ladder.csv`) and eleven segment folds (`segment_ladder.csv`).
Uniform random guessing scores 0.249.

| rung | columns | random forest, blocked | random forest, segment | logistic regression, blocked | logistic regression, segment |
| --- | --- | --- | --- | --- | --- |
| all 14 | 14 | 0.127 to 0.583 (0.334) | 0.100 to 0.446 (0.300) | 0.259 to 0.440 (0.354) | 0.160 to 0.526 (0.347) |
| no dynamometer | 12 | 0.151 to 0.499 (0.302) | 0.100 to 0.394 (0.318) | 0.237 to 0.475 (0.354) | 0.108 to 0.638 (0.338) |
| no analyzer gases | 8 | 0.200 to 0.497 (0.294) | 0.053 to 0.372 (0.281) | 0.146 to 0.347 (0.218) | 0.039 to 0.446 (0.192) |
| no wideband lambda | 6 | 0.160 to 0.437 (0.282) | 0.011 to 0.424 (0.261) | 0.082 to 0.225 (0.176) | 0.000 to 0.417 (0.166) |
| dedicated PIDs only | 4 | 0.188 to 0.435 (0.321) | 0.009 to 0.589 (0.275) | 0.075 to 0.176 (0.143) | 0.000 to 0.425 (0.132) |

- **The two designs agree.**
  At every rung the two means are within 0.05 of each other, and they lead to the same reading below.
  They are two ways of splitting the same file, so this is agreement and not independent confirmation.

- **Random forest: no rung can be told apart from another, in either design.**
  Every pair of rungs overlaps in its fold range, adjacent or not.
  All fourteen columns against the four PIDs is a mean drop of +0.013 on the blocked folds (3 of 5 folds, *p* = 0.846) and +0.025 on the segment folds (7 of 11 folds, *p* = 0.616).
  The closest any single step comes is losing the analyzer gases on the segment folds: +0.038, 9 of 11 folds, *p* = 0.082.
  So no cost of restriction has been established (`ladder_folds.csv`, `segment_ladder_folds.csv`).

- **Logistic regression falls, mostly when the analyzer gases are removed.**
  All fourteen columns against the four PIDs is a mean drop of +0.211 on the blocked folds (5 of 5 folds, *p* = 0.005) and +0.215 on the segment folds (9 of 11 folds, *p* = 0.002).
  The analyzer-gases step alone is +0.136 (5 of 5 folds, *p* = 0.012) and +0.146 (8 of 11 folds, *p* = 0.034).
  Its three narrowest rungs average below random guessing in both designs.
  Two cautions: on the segment folds the top and bottom fold ranges overlap, which they did not on the blocked folds, and each model has five such tests with no correction applied.

- **On the segment folds, no rung is established above random guessing by the protocol's range rule.**
  Every segment fold range in the table covers 0.249, including the one for all fourteen columns, whose mean sits 0.05 (random forest) and 0.10 (logistic regression) above it.
  "No cost established" has to be read with that in mind: the ladder had little to lose, and the result does not show that the port columns match the laboratory set.

**Three classes, low voltage left out, on the segment folds.**
Uniform random guessing scores 0.331 here, so these scores are not comparable with the four-class ones directly (`segment_ladder.csv`).

| rung | columns | random forest | logistic regression |
| --- | --- | --- | --- |
| all 14 | 14 | 0.224 to 0.694 (0.432) | 0.265 to 0.705 (0.501) |
| no dynamometer | 12 | 0.165 to 0.555 (0.362) | 0.148 to 0.849 (0.489) |
| no analyzer gases | 8 | 0.038 to 0.565 (0.359) | 0.052 to 0.673 (0.275) |
| no wideband lambda | 6 | 0.012 to 0.523 (0.340) | 0.000 to 0.635 (0.249) |
| dedicated PIDs only | 4 | 0.015 to 0.769 (0.362) | 0.000 to 0.597 (0.199) |

- **The reading is the same with the repeated class removed.**
  Random forest: all fourteen columns against the four PIDs is +0.070, 6 of 11 folds, *p* = 0.151.
  Logistic regression: +0.301, 9 of 11 folds, *p* = 0.002, with +0.214 of it at the analyzer-gases step (8 of 11 folds, *p* = 0.035).
  Every fold range again covers guessing.
  The widest rung's mean sits 0.10 (random forest) and 0.17 (logistic regression) above guessing, against 0.05 and 0.10 with four classes.

- **The lean and low-voltage confusion is the duplication, not a detection limit.**
  At the port-only rung on the blocked folds, 44% of true low voltage is predicted as lean mixture and 24% as itself (`port_confusion.csv`).
  The two classes have identical MAP and TPS values and near-identical segment means on every other column, so a model has nothing to separate them on.
  This is a property of the dataset. **It must not be reported as a limit of the OBD-II port.**

- **Two port columns cannot be told apart from all four.**
  On the blocked folds, engine speed and MAP alone score 0.208 to 0.385 (0.311), road speed and TPS alone 0.221 to 0.404 (0.332), and all four 0.188 to 0.435 (0.321) (`port_subsets.csv`).

## Known defects

- **`results/week1_structure.json` still carries `"rpm independent rows": 116`.**
  That figure assumed a row-to-row smoothness that `segment_lag1.csv` later showed is not there.
  It stays because the committed run produced it, and it should not be cited.

Earlier claims that no longer stand:

| earlier claim | what replaced it |
| --- | --- |
| Consecutive rows are near copies of one another | Inside a segment, lag-1 is near zero for twelve of the fourteen columns |
| Engine speed is worth about 116 independent rows | 42 distinct operating points |
| Engine speed and road speed are one quantity recorded twice | They are tied by the single gear used; inside a segment their correlation averages 0.06 |
| Low voltage leaves more unburnt fuel than lean | On the 14,000 matched rows it reverses: median HC is 164.55 for low voltage against 164.66 for lean. The check was removed from `label_map.py` on 10 November 2026 |
| The file holds 57 segments | 56, of which 42 are distinct |
| Restricting to the four PIDs costs almost nothing | No cost has been established; the rungs cannot be told apart |
