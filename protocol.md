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

- **2 November 2026 — the ladder has five rungs, not six.** The line above says six.
  `src/audit.py` defines five: all 14, no dynamometer, no analyzer gases, no wideband lambda, dedicated PIDs only.
  A sixth rung was never written, and the ladder has only ever been run with five.
  The nesting assertion in `audit.py` holds over the five that exist, so no result depends on the miscount,
  but the number above was wrong when it was written and is left as written.

- **2 November 2026 — the purge band stays at 500, from a refined figure.** The line above gives TPS at 0.9986.
  The committed run gives TPS at 0.998314 in the low-voltage block (`week1_lag1.csv`), which is the largest block-level lag-1 in the file.
  `purge_width()` derives the band from that value rather than from a number typed in here, and it still rounds to 500, so the design is unchanged.
  The column named above was the right one.

- **2 November 2026 — added a paired *t*-test across the five matched folds** for every adjacent rung pair and for the top-to-bottom comparison.
  This is an addition, not a replacement to prior work. `scripts/ladder.py` now writes `ladder_folds.csv` so the per-fold scores exist to test.
  Five pairs is a small sample and the test is reported as such.

- **2 November 2026 — both "what would change my mind" conditions fired, and were
  reported.** Adjacent rungs do overlap in their fold ranges on the random forest, so no drop between them is claimed.
  The paired test agrees, with the full top-to-bottom comparison at*p* = 0.846.
  And the lowest rung's fold range does cover random guessing, so the port-only set is reported as carrying no established fault signal in this dataset.
  Logistic regression is the one model that does fall across the ladder, and it ends at 0.143.

- **10 November 2026 — the three-class adjustment above is the wrong one.**
  "Labels 2 and 3 merged" was written on the assumption that those two classes were hard to separate.
  They are not merely hard to separate: the low-voltage block's MAP and TPS columns are bit-identical to the lean block's, offset by one segment, across all 14,000 rows.
  Merging two classes when one is a copy of the other hides the problem inside a better-looking score.
  The three-class run that matters drops the low-voltage block instead, and has not yet been run.
  The merged figure stays in `ladder.csv` as `three_class_f1` because it is what the committed run produced, and it should not be reported as the three-class result.

- **10 November 2026 — folds should hold out whole segments.**
  The blocked split above cuts each class block into five row spans.
  Whole-segment folds are a better match to how the file was recorded and make the purge band unnecessary.
  When that rerun happens, the fourteen copied pairs in `duplication.md` have to be held out together
  (lean segment *k*+1 with low-voltage segment *k*) or the split puts a segment and its own copy on opposite sides and reintroduces the leakage this design exists to prevent.
  Nothing above is withdraw until that run exists and is reported beside the current one.
