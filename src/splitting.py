# Splitting the file into training and test folds without leaking.

# BlockedSplit cuts every class block into k pieces, and fold k tests piece k of every block
# every fold holds all four classes
# every test piece is one continuous stretch of the recording
# the rows just before and after a test piece (near copies) are dropped from training. That dropped band is the purge.

from src.data_io import class_runs
import numpy as np
import pandas as pd
from src.data_io import class_runs

def purge_width(lag1_csv):
    # Rows for the slowest week 1 column to lose half its lag-1 correlation, rounded up to the next 100
    slowest = pd.read_csv(lag1_csv)["lag1"].max()
    return int(np.ceil(np.log(0.5) / np.log(slowest) / 100) * 100)
    
class BlockedSplit:
    def __init__(self, k=5, purge=0):
        self.k = k
        self.purge = purge
    def get_n_splits(self, X=None, y=None, groups=None):
        return self.k
    def split(self, X, y, groups=None):
        labels = np.asarray(y)
        runs = class_runs(labels)            # found once, not once per fold
        for fold in range(self.k):
            is_test = np.zeros(len(labels), dtype=bool)
            is_dropped = np.zeros(len(labels), dtype=bool)   # test piece plus purge band
          
            for start, end, _ in runs:
                edges = np.linspace(start, end, self.k + 1).astype(int)
                piece_start, piece_end = edges[fold], edges[fold + 1]
                is_test[piece_start:piece_end] = True

                # the band stays inside this block
                band_start = max(start, piece_start - self.purge)
                band_end = min(end, piece_end + self.purge)
                is_dropped[band_start:band_end] = True

            yield np.flatnonzero(~is_dropped), np.flatnonzero(is_test)
          
def check_split(labels, splitter):
    # The four things that must be true before I trust any number this splitter gives
    labels = np.asarray(labels)
    runs = class_runs(labels)
    times_tested = np.zeros(len(labels), dtype=int)
    checks = {"every fold holds all four classes": True,
              "each test piece is one continuous stretch": True,
              "no training row inside a purge band": True}

    for train, test in splitter.split(None, labels):
        times_tested[test] += 1
        if len(set(labels[test])) != len(set(labels)):
            checks["every fold holds all four classes"] = False

        for start, end, _ in runs:
            piece = test[(test >= start) & (test < end)]
            if piece[-1] - piece[0] + 1 != len(piece):
                checks["each test piece is one continuous stretch"] = False
            band = np.arange(max(start, piece[0] - splitter.purge),
                             min(end, piece[-1] + splitter.purge + 1))
            if np.isin(band, train).any():
                checks["no training row inside a purge band"] = False

    checks["every row is tested exactly once"] = bool((times_tested == 1).all())
    return checks
