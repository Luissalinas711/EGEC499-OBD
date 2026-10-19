# AVAILABILITY AUDIT
# What a car could actually supply for each of the 14 columns, so every later script uses the same feature sets. 
# The tiers:
#   port           a standard OBD-II PID reports the same quantity
#   substitutable  a car can supply it, but only some cars, from a different instrument, or by calculation
#   laboratory     needs the dynamometer or the gas analyser; no car reports it

# These are my judgements, not measurements. 
# Nothing in the dataset confirms them, so the reasons are one line each here. the full argument will be carried out later

AUDIT = {
    # column       tier              where a car could get it
    "rpm":         ("port",          "PID 0x0C engine speed"),
    "speed":       ("port",          "PID 0x0D vehicle speed"),
    "map":         ("port",          "PID 0x0B manifold pressure (this data is in volts)"),
    "tps":         ("port",          "PID 0x11 throttle position (this data is in volts)"),
    "cons_lph":    ("substitutable", "PID 0x5E fuel rate on some cars, or from MAF"),
    "cons_l100km": ("substitutable", "calculated from fuel rate and speed"),
    "lambda_":     ("substitutable", "wideband PIDs 0x24 to 0x2B, 0x34 to 0x3B, some cars"),
    "afr":         ("substitutable", "lambda times a constant, so it follows lambda"),
    # Moved out of an "undecided" tier on 9 October:
    # this column is exhaust oxygen from the gas analyser, which no port reports, and the nearest thing a car does report is lambda from the wideband sensor (already its own column above)
    "o2":          ("laboratory",    "gas analyser only; a car reports lambda instead"),
    "co":          ("laboratory",    "gas analyser only"),
    "hc":          ("laboratory",    "gas analyser only"),
    "co2":         ("laboratory",    "gas analyser only"),
    "force":       ("laboratory",    "dynamometer only (PID 0x04 load is a loose proxy)"),
    "power":       ("laboratory",    "dynamometer only"),
}

# RESTRICTION LADDER
# Each rung removes one instrument or one assumption, and every rung sits inside the one before it, so any drop in score between two rungs has a single named cause. 
# The name of each rung says what was taken away to get there

RUNGS = {
    "all 14 (laboratory)": ["rpm", "speed", "map", "tps", "cons_lph", "cons_l100km",
                            "lambda_", "afr", "o2", "co", "hc", "co2", "force", "power"],
    "no dynamometer":      ["rpm", "speed", "map", "tps", "cons_lph", "cons_l100km",
                            "lambda_", "afr", "o2", "co", "hc", "co2"],
    "no analyser gases":   ["rpm", "speed", "map", "tps", "cons_lph", "cons_l100km",
                            "lambda_", "afr"],
    "no wideband lambda":  ["rpm", "speed", "map", "tps", "cons_lph", "cons_l100km"],
    "dedicated PIDs only": ["rpm", "speed", "map", "tps"],
}

# Two things that would quietly invalidate the ladder if they were ever false, so they are  checked here:
# 1. A misspelled column would surface as a pandas error during the run (which can take several minutes or longer)
# 2. a rung that is not nested inside the one above it would give a drop in score (potentially with more than one possible cause)

_names = list(RUNGS)
for _rung, _columns in RUNGS.items():
    assert not set(_columns) - set(AUDIT), \
        f"{_rung} names a column that is not in AUDIT: {set(_columns) - set(AUDIT)}"
for _bigger, _smaller in zip(_names, _names[1:]):
    assert set(RUNGS[_smaller]) < set(RUNGS[_bigger]), f"{_smaller} is not inside {_bigger}"
