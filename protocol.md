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
