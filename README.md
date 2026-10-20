# EGEC 499: From Data to Device

**Student:** Luis Rey Salinas Jr.
**Mentor:** Dr. Yoonsuk Choi
**School:** California State University, Fullerton
**Department:** Electrical Engineering

Which engine faults stay detectable using only measurements an OBD-II port can supply,
how much detection performance is lost as the measurements are restricted, and do real cars supply what is left?

Fall 2026 is the analysis on an existing dataset. Spring 2027 is the physical build with an ESP32-based reader, and a survey of what real cars report.

## Data

EngineFaultDB (Vergara et al., IEEE Access 11, 2023, DOI 10.1109/ACCESS.2023.3331316,GPL-3.0) at https://github.com/leoxthomas/EngineFaultDB. 

The CSV is not committed. The startup cell downloads it into data/raw/ the first time a session runs, and skips it afterwards; 
the download URL is set at the top of colab/startup_cell.py.

Needs pandas, numpy, scikit-learn and matplotlib. Everything runs in Google Colab with no extra installation.

## Layout

Three folders, split by how each file is used.

| path | kind | what it holds |
| --- | --- | --- |
| `src/config.py` | module | paths, column names, fault names |
| `src/data_io.py` | module | `load()`, `class_runs()`, and `save_result()` / `load_result()` |
| `src/audit.py` | module | the availability tier for each column, and the restriction ladder |
| `src/splitting.py` | module | `BlockedSplit`, `check_split`, `purge_width` |
| `scripts/week1_verify.py` | script | checks the flagged items against the plan |
| `scripts/label_map.py` | script | confirms which numeric label is which fault |
| `scripts/folds.py` | script | checks the splitter, measures operating-point drift |
| `scripts/ladder.py` | script | the restriction ladder, two models, three split designs |
| `scripts/ladder_report.py` | script | reads `ladder.csv`, writes the tables and the figure |
| `scripts/diagnostics.py` | script | four checks on the port-only rung |
| `colab/startup_cell.py` | cell | mounts Drive, sets up git, clones the repo, fetches the data |
| `colab/finish_cell.py` | cell | copies results into the repo, commits and pushes |

Modules in `src/` are imported and print nothing on their own. 
Scripts in `scripts/` are run directly.
The two files in `colab/` are pasted into the notebook rather than executed from the repository; fill in the details block at the top of `startup_cell.py` first.

## Running it

Run `colab/startup_cell.py` as the first cell of the session, then each script below in order, then `colab/finish_cell.py` as the last cell.

| step | script | produces | needs |
| --- | --- | --- | --- |
| 1 | `scripts/week1_verify.py` | `week1_lag1.csv`, `week1_structure.json` | the CSV |
| 2 | `scripts/label_map.py` | `label_evidence.csv`, `label_evidence.png` | the CSV |
| 3 | `scripts/folds.py` | `fold_drift.csv` | step 1 |
| 4 | `scripts/ladder.py` | `ladder.csv` | step 1 |
| 5 | `scripts/ladder_report.py` | `ladder.png` | step 4 |
| 6 | `scripts/diagnostics.py` | `port_rung_folds.csv`, `matched_separation.csv`, `within_recording_drift.csv` | step 1 |

Steps 2, 3 and 6 are quick to run. Step 4 is the only slow one, which is why the ladder writes a CSV.
Reporting is a separate script so that the figure and the tables can be changed and re-run.

These paths are Colab's. `src/config.py` writes results to `/content/drive/MyDrive/`, so running anywhere else means changing `DRIVE` there first.

## Editing it

Scripts in `scripts/` are read fresh every time they run, so editing one takes effect immediately.
The four modules in `src/` are not. 
Once `config.py`, `data_io.py`, `splitting.py` or`audit.py` has been imported, Python keeps that copy for the rest of the session, 
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

The file is a time recording, not a shuffled sample. 
Consecutive rows are the same engine a fraction of a second apart, 
so a standard shuffled split puts near-copies of one instant on both sides and tests the model on records it has effectively already seen.

`BlockedSplit` cuts each class block into five contiguous pieces and tests piece *k* of every block in fold *k*, 
so each fold holds all four classes and every test region is one continuous span of time. 
Rows beside a test piece are dropped from training; the width of that purge band is the half-life of the slowest column's lag-1 correlation, 500 rows.
Four properties are asserted before any score is used.

`audit.py` checks four things on import: 
every rung names a real column, each rung nests inside the one above it, the widest rung is every audited column, and the narrowest rung is exactly the port tier. 
The last one ties the ladder to the availability tiers, so a column cannot be reclassified without the ladder following.

Macro F1 is the primary metric. Random guessing scores about 0.25 on these four classes.
Results are reported as the range across the five folds, not as a single number.

## Findings so far

As of 19 October 2026.

- **Leakage is worth 0.42 macro F1** at the full fourteen columns: 0.755 under a shuffled split against 0.334 under a blocked split with the purge band.
  Almost all of the gap comes from breaking the block structure rather than from rows adjacent to the test piece.
- **Restriction to the four dedicated OBD-II PIDs costs almost nothing**
  , 0.334 to 0.321, but the fold range at that rung covers random guessing, so no fault signal is established there.
- **The fault label and the recording session cannot be separated.**
  The four labels sit in four contiguous blocks, and the paper describes each fault being induced and then recorded, so on that reading the label and the session are the same variable.
  On engine speed, every one of the four blocks separates its own two halves better, 0.665 to 0.800, than any two faults separate, 0.610.
- **MAP and TPS are recorded in volts**, not the kPa and percent the paper states; its own Table 5 gives ranges of 0.45 to 4.55 and 0.38 to 4.05.


