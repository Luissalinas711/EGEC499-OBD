# Evaluation protocol

Written on: 4 October 2026, before `scripts/ladder.py` was first run and before any restricted-feature result existed.

Committed on: 10 November 2026. The delay was an oversight, not a revision to prior work.

## Data
- EngineFaultDB_Final.csv, the copy whose SHA-256 is in data/DATA_SOURCE.md.
- File order is never changed. The loader stops if a column name is unexpected.

## Tasks
- Four classes: labels 0 to 3, named as recorded in results/label_medians.csv.
- Three classes: labels 2 and 3 merged, reported alongside the four-class result.

## Feature sets
- The six nested rungs in src/audit.py, run in that order, all of them, every time.

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

- **2 November 2026: the ladder has five rungs, not six.**
  `src/audit.py` defines five: all 14, no dynamometer, no analyzer gases, no wideband lambda, dedicated PIDs only.
  A sixth was never written, so the count above was wrong when it was written and is left as written.
  No result depends on it.

- **2 November 2026: a paired *t*-test on the five matched folds was added.**
  It is run for every adjacent pair of rungs and for the top rung against the bottom one, using the per-fold scores in `ladder_folds.csv`.
  It adds to the fold range and does not replace it.
  Five pairs is a small sample, and the test is reported as such.

- **2 November 2026: both conditions under "What would change my mind" were met, and are reported.**
  Adjacent rungs: on the random forest every adjacent pair overlaps in its fold range, so no drop between rungs is claimed.
  The paired test agrees, with the top rung against the bottom one at *p* = 0.846.
  Lowest rung: the random forest's fold range there is 0.188 to 0.435, which covers random guessing at 0.249,
  so the port-only set is reported as carrying no established fault signal in this dataset.
  Logistic regression is the one model that falls across the ladder: its fold range is 0.259 to 0.440 at the top rung and 0.075 to 0.176 at the bottom, *p* = 0.005.

- **10 November 2026: merging labels 2 and 3 is the wrong three-class adjustment.**
  "Labels 2 and 3 merged" was written on the assumption that those two classes were hard to separate.
  It is more than that: the low-voltage block's MAP and TPS columns are identical to the lean block's, offset by one segment, across all 14,000 rows (`duplication.md`).
  Merging two classes when one repeats the other hides the problem inside a better-looking score.
  The three-class run that matters drops the low-voltage block, and it has not been run yet.
  `three_class_f1` in `ladder.csv` is the merged figure. It stays because the committed run produced it, and it should not be reported as the three-class result.

- **10 November 2026: the next run will hold out whole segments.**
  The blocked split above cuts each class block into five row spans.
  Whole 1000-row segments match how the file was recorded and need no purge band.
  The fourteen repeated pairs in `duplication.md` (lean segment *k*+1 with low-voltage segment *k*) have to be held out together,
  or a segment and its repeat land on opposite sides of the split.
  Nothing above is withdrawn until that run exists and is reported beside the current one.
  The rules for that run are fixed in the next section.

## Segment-based rerun

Written on 11 November 2026, before any segment-based score had been read.
`scripts/segment_ladder.py` was run once beforehand with its output hidden, only to confirm that it finishes and writes its two files.
`src/segment_map.py`, which fixes the segments and the folds, was committed at 10:08 that morning, before the run at 10:32.
The rest of this section was committed after the run, so for everything but the folds the git history cannot show that the rules came first.
Everything above still applies unless a line here replaces it.

### Unit
- The unit is the segment. All 56 are listed row by row in `src/segment_map.py`: 16 no fault, 11 rich mixture, 15 lean mixture, 14 low voltage.
- A boundary is the row where the columns step together. It is read from the measurements, never from a score.
- Every segment is 1000 rows, with two exceptions.
  The first and third rich segments are 999 rows.
  The last row of the file repeats the row before it, and stays with low-voltage segment 14.

### Groups
- A segment is never split between training and test.
- Lean segment *n* + 1 and low-voltage segment *n* are always tested in the same fold, for *n* = 1 to 14, because their MAP and TPS columns are identical (`duplication.md`).
- That leaves 42 groups: 16 no fault, 11 rich mixture, lean segment 1 on its own, and the 14 pairs.

### Folds
- 11 folds.
  Why 11: rich mixture has 11 segments, the fewest of any class, so 11 is the most folds in which every fold can test a whole segment of every class.
- Within each class, segments are dealt to folds 1 to 11 in file order, starting again at fold 1.
  A low-voltage segment goes to the fold of its paired lean segment.
  This is fixed here and written out in `src/segment_map.py`. It was not tuned.
- Folds 1 to 5 test between 5,000 and 7,001 rows and folds 6 to 11 test 4,000, because three of the classes have more than 11 segments.
- No purge band, because a whole segment is held out and its neighbors in the file are other segments.
- The shuffled and no-purge controls are not rerun. They stand as reported above.

### Models, rungs and metric
- Unchanged: the same two models with the same settings, the same five rungs, and macro F1.

### What gets reported
- Macro F1 as the range across the 11 folds, lowest to highest, with the mean after it.
- The fold-by-fold drop for each adjacent pair of rungs and for the top rung against the bottom one, with the paired *t*-test on those 11 drops.
  Eleven pairs is still a small sample, and the test is reported as such.
- The five-fold blocked result in the same table, so the two designs can be read side by side.
- Recall for each class. Every fold score is kept in `segment_ladder_folds.csv`.

### Three-class view
- Four classes stays the primary result.
- The three-class view leaves the low-voltage rows out of training and out of test. It does not merge them into lean mixture.
- Same folds, same models, same rungs. Uniform random guessing scores 0.331 on these three classes.

### What would change my mind
- The two conditions above apply to this run unchanged, with 11 folds in place of 5.
- If the segment-based result and the blocked result disagree, both are reported and the disagreement is stated.
  Neither replaces the other without a dated line here.
- The lean and low-voltage confusion is reported as a property of this dataset, not as a detection limit.

### Result, run on 11 November 2026
- The full tables are in the README, `segment_ladder.csv` and `segment_ladder_folds.csv`. This entry records how the rules above came out.
- **Adjacent rungs.** In both models and both views, every adjacent pair of rungs overlaps in its fold range, so no drop between adjacent rungs is claimed from the ranges.
  On the paired test the random forest has no step below *p* = 0.08.
  Logistic regression has one, losing the analyzer gases: +0.146 in 8 of 11 folds, *p* = 0.034, with four classes, and +0.214 in 8 of 11 folds, *p* = 0.035, with three.
- **Top rung against bottom rung.**
  Random forest: +0.025 in 7 of 11 folds, *p* = 0.616, with four classes, and +0.070 in 6 of 11 folds, *p* = 0.151, with three.
  Logistic regression: +0.215 in 9 of 11 folds, *p* = 0.002, with four classes, and +0.301 in 9 of 11 folds, *p* = 0.002, with three.
  Its top and bottom fold ranges overlap here, 0.160 to 0.526 against 0.000 to 0.425 with four classes, which they did not on the blocked folds.
- **Lowest rung against guessing.** The port-only fold range covers random guessing for both models in both views:
  0.009 to 0.589 and 0.000 to 0.425 against 0.249, and 0.015 to 0.769 and 0.000 to 0.597 against 0.331.
  So the port-only set is again reported as carrying no established fault signal in this dataset.
  The same is true of every other rung, including all 14 columns: every fold range in this run covers guessing.
- **Against the blocked result.** With four classes the two designs' means are within 0.05 of each other at every rung, and both lead to the same reading.
  The one difference is the overlap noted above. Both results stay reported.
  They split the same file, so their agreement is not independent confirmation.
- **Three-class view.** This is the run the 10 November entry said had not been done. It does not change the reading.
- The paired tests are not corrected for there being five per model and view.

## Operating-point check

Written on 11 November 2026, after the segment-based result and before `scripts/operating_points.py` was run in the notebook.
The matching rule below was set from engine speed, MAP and TPS alone, so how many pairs it matches was already known when this was written.
What the other columns do at those pairs was not known. The script was run once beforehand to confirm that it writes its file, and those columns were not read.

### Question
- Were different faults recorded at the same operating points?
- Where they were, do the other columns differ between the classes by more than they differ within a class?

### Rule
- A segment's operating point is its mean engine speed, MAP and TPS.
- The gap between two segments on a column is the difference between their means, divided by the average of their two standard deviations.
  This is the gap used in `duplication.md`.
- The operating-point distance between two segments is the largest of their three gaps on engine speed, MAP and TPS.
- Matched means a distance of at most 1. Loosely matched means a distance of at most 2. Both are reported, and neither was tuned.
- Low voltage is left out, because its segments repeat lean ones. That leaves 42 segments in three classes, and 861 pairs.

### What gets reported
- How many pairs of segments from different classes are matched and loosely matched, and which pairs they are.
- For each segment, whether the nearest segment outside its own fold belongs to its own class.
  This is what operating point alone would predict for a held-out segment.
- At the matched and loosely matched pairs, the gap on each of the other eleven columns, for pairs from different classes beside pairs from the same class.

### How it is read
- A column separates two classes at a shared operating point if its smallest gap between the classes is larger than its largest gap among same-class pairs.
- The counts are small: 3 matched pairs and 10 matched or loosely matched pairs from different classes, beside 3 and 6 from the same class.
  So this is a description and not a test, and no *p* value is attached.
- Two segments at the same operating point can still differ in conditions the file does not record, so a separation is evidence of a fault signature and not proof of one.

### What would change my mind
- If no column separates the classes at the shared operating points, I report that the file shows no fault signature apart from operating point.
- If some columns do, I report which ones and for which classes.
  I do not extend that to operating points where no pair is shared.
