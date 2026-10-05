# THE AVAILABILITY AUDIT
# What a car could actually supply for each of the 14 columns, so every later script uses the same feature sets
# The tiers:
#   port           a standard OBD-II PID reports it
#   substitutable  a car can supply it, but only some cars
#   undecided      a real argument either way
#   laboratory     needs the dynamometer or the gas analyser; no car reports it

# NOTE: These are my judgements, not measurements

AUDIT = {
    # column       tier              where a car could get it
    "rpm":         ("port",          "PID 0x0C engine speed"),
    "speed":       ("port",          "PID 0x0D vehicle speed"),
    "map":         ("port",          "PID 0x0B manifold pressure (in volts)"),
    "tps":         ("port",          "PID 0x11 throttle position (in volts)"),
    "cons_lph":    ("substitutable", "PID 0x5E fuel rate on some cars, or from MAF"),
    "cons_l100km": ("substitutable", "calculated from fuel rate and speed"),
    "lambda_":     ("substitutable", "PIDs 0x24 to 0x2B, 0x34 to 0x3B, some cars"),
    "afr":         ("substitutable", "lambda times a constant, so it follows lambda"),
    "o2":          ("undecided",     "analyser %O2; a car sensor mostly says rich or lean"),
    "co":          ("laboratory",    "gas analyser only"),
    "hc":          ("laboratory",    "gas analyser only"),
    "co2":         ("laboratory",    "gas analyser only"),
    "force":       ("laboratory",    "dynamometer only (PID 0x04 loosely attempts to copy this)"),
    "power":       ("laboratory",    "dynamometer only"),
}

# THE RESTRICTION LADDER
# Each rung removes one instrument or one assumption
# every rung sits inside the one before it, so any drop in score between two rungs has a single named cause. 
# The name of each rung says what was taken away 

RUNGS = {
    "all 14 (laboratory)": ["rpm", "speed", "map", "tps", "cons_lph", "cons_l100km",
                            "lambda_", "afr", "o2", "co", "hc", "co2", "force", "power"],
    "no dynamometer":      ["rpm", "speed", "map", "tps", "cons_lph", "cons_l100km",
                            "lambda_", "afr", "o2", "co", "hc", "co2"],
    "no analyser gases":   ["rpm", "speed", "map", "tps", "cons_lph", "cons_l100km",
                            "lambda_", "afr", "o2"],
    "no analyser O2":      ["rpm", "speed", "map", "tps", "cons_lph", "cons_l100km",
                            "lambda_", "afr"],
    "no wideband lambda":  ["rpm", "speed", "map", "tps", "cons_lph", "cons_l100km"],
    "dedicated PIDs only": ["rpm", "speed", "map", "tps"],
}

# A misspelled column would come up as a pandas error several minutes into the run
# a rung that is not nested inside the  one above it would give a drop in score with more than one possible cause

_names = list(RUNGS)
for _rung, _columns in RUNGS.items():
    assert not set(_columns) - set(AUDIT), \
        f"{_rung} names a column that is not in AUDIT: {set(_columns) - set(AUDIT)}"
for _bigger, _smaller in zip(_names, _names[1:]):
    assert set(RUNGS[_smaller]) < set(RUNGS[_bigger]), f"{_smaller} is not inside {_bigger}"
