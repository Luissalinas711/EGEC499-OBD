# The 56 segments of the file, and the fold each one is tested in.
# protocol.md says how the boundaries and the folds were chosen.

import numpy as np

FOLDS = 11
LEAN = 2
LOW_VOLTAGE = 3

# label, segment number within its class, first row, last row, fold
SEGMENTS = [
    # no fault, 16 segments
    (0,  1,     0,   999,  1),
    (0,  2,  1000,  1999,  2),
    (0,  3,  2000,  2999,  3),
    (0,  4,  3000,  3999,  4),
    (0,  5,  4000,  4999,  5),
    (0,  6,  5000,  5999,  6),
    (0,  7,  6000,  6999,  7),
    (0,  8,  7000,  7999,  8),
    (0,  9,  8000,  8999,  9),
    (0, 10,  9000,  9999, 10),
    (0, 11, 10000, 10999, 11),
    (0, 12, 11000, 11999,  1),
    (0, 13, 12000, 12999,  2),
    (0, 14, 13000, 13999,  3),
    (0, 15, 14000, 14999,  4),
    (0, 16, 15000, 15999,  5),
    # rich mixture, 11 segments
    (1,  1, 16000, 16998,  1),
    (1,  2, 16999, 17998,  2),
    (1,  3, 17999, 18997,  3),
    (1,  4, 18998, 19997,  4),
    (1,  5, 19998, 20997,  5),
    (1,  6, 20998, 21997,  6),
    (1,  7, 21998, 22997,  7),
    (1,  8, 22998, 23997,  8),
    (1,  9, 23998, 24997,  9),
    (1, 10, 24998, 25997, 10),
    (1, 11, 25998, 26997, 11),
    # lean mixture, 15 segments
    (2,  1, 26998, 27997,  1),
    (2,  2, 27998, 28997,  2),
    (2,  3, 28998, 29997,  3),
    (2,  4, 29998, 30997,  4),
    (2,  5, 30998, 31997,  5),
    (2,  6, 31998, 32997,  6),
    (2,  7, 32998, 33997,  7),
    (2,  8, 33998, 34997,  8),
    (2,  9, 34998, 35997,  9),
    (2, 10, 35998, 36997, 10),
    (2, 11, 36998, 37997, 11),
    (2, 12, 37998, 38997,  1),
    (2, 13, 38998, 39997,  2),
    (2, 14, 39998, 40997,  3),
    (2, 15, 40998, 41997,  4),
    # low voltage, 14 segments
    (3,  1, 41998, 42997,  2),
    (3,  2, 42998, 43997,  3),
    (3,  3, 43998, 44997,  4),
    (3,  4, 44998, 45997,  5),
    (3,  5, 45998, 46997,  6),
    (3,  6, 46998, 47997,  7),
    (3,  7, 47998, 48997,  8),
    (3,  8, 48998, 49997,  9),
    (3,  9, 49998, 50997, 10),
    (3, 10, 50998, 51997, 11),
    (3, 11, 51998, 52997,  1),
    (3, 12, 52998, 53997,  2),
    (3, 13, 53998, 54997,  3),
    (3, 14, 54998, 55998,  4),
]


def fold_of_each_row():
    # The fold number of every row, in file order
    folds = np.zeros(SEGMENTS[-1][3] + 1, dtype=int)
    for label, number, first, last, fold in SEGMENTS:
        folds[first:last + 1] = fold
    return folds


def check_segments(df):
    # The things that must be true of the data before a score from these folds is used
    labels = df["fault"].to_numpy()
    folds = fold_of_each_row()
    rows_of = {(label, number): (first, last) for label, number, first, last, fold in SEGMENTS}

    # Nothing else can be checked against a file of another length
    if len(folds) != len(labels):
        return {"the segments cover every row of the file": False}

    checks = {"the segments cover every row of the file": True,
              "every segment holds one class": True,
              "every fold tests all four classes": True,
              "paired lean and low-voltage segments match on MAP and TPS": True}

    for label, number, first, last, fold in SEGMENTS:
        if not (labels[first:last + 1] == label).all():
            checks["every segment holds one class"] = False
        # Low-voltage segment n is compared with lean segment n + 1, over the rows they share
        if label == LOW_VOLTAGE:
            lean_first, lean_last = rows_of[(LEAN, number + 1)]
            rows = lean_last - lean_first + 1
            low = df[["map", "tps"]].iloc[first:first + rows].to_numpy()
            lean = df[["map", "tps"]].iloc[lean_first:lean_last + 1].to_numpy()
            if not np.array_equal(low, lean):
                checks["paired lean and low-voltage segments match on MAP and TPS"] = False

    for fold in range(1, FOLDS + 1):
        if len(set(labels[folds == fold])) != len(set(labels)):
            checks["every fold tests all four classes"] = False
    return checks


# CHECKS ON THE TABLE ITSELF
# 1. Segments follow one another with no gap and no overlap, starting at row 0
expected_first = 0
for label, number, first, last, fold in SEGMENTS:
    assert first == expected_first and last >= first, f"gap or overlap at row {first}"
    expected_first = last + 1

# 2. Within a class, segments are numbered 1, 2, 3, ... in file order
for label in sorted({segment[0] for segment in SEGMENTS}):
    numbers = [segment[1] for segment in SEGMENTS if segment[0] == label]
    assert numbers == list(range(1, len(numbers) + 1)), f"numbering of label {label}"

# 3. Folds are dealt in turn within a class: segment 1 to fold 1, segment 12 back to fold 1
# 4. A low-voltage segment n sits in the fold of lean segment n + 1
fold_of = {(label, number): fold for label, number, first, last, fold in SEGMENTS}
for (label, number), fold in fold_of.items():
    if label == LOW_VOLTAGE:
        assert fold == fold_of[(LEAN, number + 1)], f"low voltage {number} is not with lean {number + 1}"
    else:
        assert fold == (number - 1) % FOLDS + 1, f"fold of label {label} segment {number}"
