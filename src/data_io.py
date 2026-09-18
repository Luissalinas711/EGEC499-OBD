# Loading the dataset, and finding the class blocks inside it.

import numpy as np
import pandas as pd

from src import config


def load(path=None):
    # Read the CSV in file order and rename the columns.
    # Never sort or shuffle the rows, as the order carries the class blocks
    
    if path is None:
        path = config.CSV

    df = pd.read_csv(path)

    new_names = {}
    for column in df.columns:
        key = column.strip().lower()
        if key not in config.COLUMN_NAMES:
            raise KeyError(f"unexpected column in the CSV: {column}")
        new_names[column] = config.COLUMN_NAMES[key]

    df = df.rename(columns=new_names)
    df = df[[config.LABEL] + config.FEATURES]
    print(f"loaded {len(df):,} rows and {df.shape[1]} columns")
    return df


def class_runs(labels):
    # Find the blocks of rows that share a label.


    labels = np.asarray(labels)
    # np.diff is non-zero wherever the label changes, so those spots plus one are starts
    change_points = np.flatnonzero(np.diff(labels)) + 1
    starts = [0] + list(change_points)
    ends = starts[1:] + [len(labels)]
    return [(int(s), int(e), int(labels[s])) for s, e in zip(starts, ends)]


def count_label_changes(labels):
    # How many times the label column changes
    return len(class_runs(labels)) - 1
