# Evaluation protocol

Written on: 4 October 2026, before `scripts/ladder.py` was first run and before any restricted-feature result existed.

Committed on: 10 November 2026. The delay was an oversight, not a revision to prior work.

Revised on: 12 November 2026. The 4 October rules below are unchanged. The later sections were condensed to make workflow easier to follow.

## Data
- EngineFaultDB_Final.csv, the copy whose SHA-256 is in data/DATA_SOURCE.md.
- File order is never changed. The loader stops if a column name is unexpected.

## Tasks
- Four classes: labels 0 to 3, named as recorded in results/label_medians.csv.
- Three classes: labels 2 and 3 merged, reported alongside the four-class result.

## Feature sets
- The six rungs in src/audit.py, run in that order, all of them, every time.

## Split
- BlockedSplit, 5 folds, purge band of 500 rows on each side of every test piece.
  This is the design every claim rests on.
- Why 500: the half-life of the slowest column's lag-1 correlation (TPS, 0.9986), rounded up to the next 100.
- A shuffled 5-fold split runs at every rung as well. It leaks by construction, so it is the control that demonstrates the problem.

## Models (same settings on every rung, no tuning)
- Random forest, 100 trees, random_state 0.
- Logistic regression, max_iter 1000, with scaling fitted inside each training fold.

## What gets reported
- Macro F1 (primary), quoted as the range across the 5 folds, lowest to highest.
  The range is the primary figure; a mean may follow it but never stands on its own.
  Why: a test piece carries roughly 20 to 30 independent rows, so how much the folds disagree is itself a finding about what this dataset can support.
- The shuffled split's score beside the blocked range at every rung, labelled as the control.
  Retired as a basis for claims, kept as a reported figure.
- Recall for each class, and macro F1 for the three-class view.
- Baselines: always guessing the largest class (accuracy 0.29, macro F1 about 0.11) and random guessing (about 0.25).

## What would change my mind
- If adjacent rungs overlap in their fold ranges, I report that the drop between them is not established, rather than reading a difference into the means.
- If the lowest rung scores within the fold spread of random guessing,
  I report that the port-only set carries no usable fault signal here, not a tuned-up version of it.

## Changes after freezing

- **19 October 2026: the ladder went from six rungs to five.** O2 was moved from an undecided tier to the laboratory tier, so its own rung, "no analyser O2", was folded into the analyzer-gases rung. The 4 October run used six rungs, and every result reported here uses five.
- **2 November 2026: a paired *t*-test on the matched folds was added**, for each adjacent pair of rungs and for the top rung against the bottom. It adds to the fold range and does not replace it. Five pairs is a small sample, and the test is reported as such.
- **2 November 2026: both conditions under "What would change my mind" were met.**
  Random forest: adjacent rungs overlap, top against bottom is *p* = 0.846, and the lowest rung's range (0.188 to 0.435) covers guessing at 0.249. So no drop between rungs is claimed, and the port-only set is reported as carrying no established fault signal in this dataset.
  Logistic regression falls from 0.259–0.440 at the top rung to 0.075–0.176 at the bottom, *p* = 0.005.
- **10 November 2026: merging labels 2 and 3 is the wrong three-class view.** Low voltage repeats lean (`duplication.md`), so the three-class run leaves low voltage out instead. `three_class_f1` in `ladder.csv` is the merged figure and is not the three-class result.
- **10 November 2026: the next run holds out whole segments**, with each repeated lean and low-voltage pair kept together, so a segment and its repeat cannot land on opposite sides of the split. Nothing above is withdrawn; the new result is reported beside the current one. Its rules follow.

## Segment-based rerun

Written on 11 November 2026, before any segment-based score had been read.
`src/segment_map.py`, which fixes the segments and folds, was committed before the run. The rest of this section was committed after it, so for everything but the folds the git history cannot show that the rules came first.
The script was run once beforehand with its output hidden, only to confirm that it finishes.

- **Unit:** the 56 segments listed in `src/segment_map.py`. A boundary is the row where the columns step together, read from the measurements and never from a score. All are 1000 rows except rich segments 1 and 3, at 999, and the last one, which keeps the file's repeated final row.
- **Groups:** a segment is never split between training and test. Lean segment *n* + 1 and low-voltage segment *n* share a fold, because their MAP and TPS columns are identical (`duplication.md`). That leaves 42 groups.
- **Folds:** 11. Rich mixture has 11 segments, the fewest of any class, so 11 is the most folds in which every fold tests a whole segment of every class. Within each class, segments are dealt to folds in file order. This was not tuned. A fold tests between 4,000 and 7,001 rows.
- **No purge band:** a whole segment is held out, and its neighbors in the file are other segments.
- **Unchanged:** the two models and their settings, the five rungs, macro F1. The shuffled and no-purge controls are not rerun.
- **Reported:** the range across the 11 folds with the mean, the fold-by-fold drops with a paired *t*-test, recall for each class, and the blocked result alongside. Eleven pairs is still a small sample.
- **Three-class view:** low-voltage rows are left out of training and test, on the same folds. Four classes stays primary. Random guessing scores 0.331.
- **What would change my mind:** the two conditions above, with 11 folds. If the two designs disagree, both are reported, and neither replaces the other without a dated line here. The lean and low-voltage confusion is a property of this dataset, not a detection limit.

### Result, run on 11 November 2026
- **Adjacent rungs:** every adjacent pair overlaps in its fold range, in both models and both views. On the paired test the random forest has no step below *p* = 0.08. Logistic regression drops at the analyzer gases: +0.146 (8 of 11 folds, *p* = 0.034) with four classes and +0.214 (8 of 11, *p* = 0.035) with three.
- **Top rung against bottom:** random forest +0.025 (7 of 11, *p* = 0.616) with four classes and +0.070 (6 of 11, *p* = 0.151) with three. Logistic regression +0.215 and +0.301 (9 of 11, *p* = 0.002 each). Its top and bottom ranges overlap here, which they did not on the blocked folds.
- **Against guessing:** every fold range covers random guessing, at every rung, for both models and both views. The port-only set is again reported as carrying no established fault signal in this dataset.
- **Against the blocked result:** with four classes the two designs' means are within 0.05 at every rung and give the same reading. Both stay reported. They split the same file, so this is not independent confirmation.
- The paired tests are uncorrected, five per model and view. The tables are in the README and `segment_ladder.csv`.

## Operating-point check

Written on 11 November 2026 and committed at 11:42, one minute before the run.
The rule was set from engine speed, MAP and TPS alone, so how many pairs it matches was already known. What the other columns do at those pairs was not.

- **Question:** were different faults recorded at the same operating points, and where they were, do the other columns differ between classes by more than they differ within a class?
- **Operating point:** a segment's mean engine speed, MAP and TPS.
- **Gap:** the difference between two segments' means on a column, over the average of their two standard deviations, as in `duplication.md`. The distance between two segments is the largest of their three operating-point gaps.
- **Matched:** a distance of at most 1. **Loosely matched:** at most 2. Neither was tuned. Low voltage is left out because its segments repeat lean ones, leaving 42 segments and 861 pairs.
- **How it is read:** a column separates two classes if its smallest gap between them is larger than its largest gap among same-class pairs. The counts are small, so this is a description and not a test.
  Two segments at the same operating point can still differ in conditions the file does not record, so a separation is evidence of a fault signature and not proof of one.
- **What would change my mind:** if no column separates, I report no fault signature apart from operating point. If some do, I report which, and claim nothing beyond the shared points.

### Result, run on 11 November 2026
- **Shared points:** 3 of the 581 pairs from different classes are matched, and 10 are matched or loosely matched. 15 of the 42 segments have such a partner in another class, and 27 have none.
- **Nearest segment outside a segment's own fold:** it is of the segment's own class for 20 of the 42 (7 of 16 no fault, 4 of 11 rich mixture, 9 of 15 lean mixture). This is what operating point alone would predict for a held-out segment.
- **Columns that separate**, by the rule above:

| Classes | Matched pairs | Matched or loosely matched pairs |
| --- | --- | --- |
| no fault / rich mixture | force, HC (1 pair) | HC (4 pairs) |
| no fault / lean mixture | no pair | HC, CO2 (2 pairs) |
| rich / lean mixture | CO, CO2, O2, lambda (2 pairs) | CO, CO2, lambda (4 pairs) |

- **How firm:** several pass narrowly, such as CO for rich and lean mixture at 72.08 against a same-class ceiling of 70.43. The clear ones are lambda for rich and lean mixture, 6.31 against 3.90, and HC for no fault and rich mixture on the matched pair, 95.61 against 12.73.
- **Outside the rule, noted after the run:** the same-class ceiling for CO and lambda comes from one pair, rich segments 2 and 7, which differ by 70.43 on CO at a matched operating point. So engine speed, MAP and TPS do not fix the other columns even within one class. The reason has not been tested.
- The figures are in `operating_point_pairs.csv`.
