#!/usr/bin/env python3
import os

from seismic.observations import ObservationDAO

PATHS = [
    "../sample/local"
]
OUT = "csv"

obs = {}

for p in PATHS:
    obs[p] = {f: ObservationDAO(os.path.join(p, f)) for f in os.listdir(p)}
    os.mkdir("/tmp")