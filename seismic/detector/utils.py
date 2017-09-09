import pandas as pd
import numpy as np
from matplotlib.ticker import FuncFormatter


def make_series(data, sampling_rate, start_time=0):
    end_time = len(data) * (1000 / sampling_rate) + start_time
    timestamps = np.linspace(start_time, end_time, num=len(data))
    rng = pd.to_datetime(timestamps, unit="ms")
    return pd.Series(data=data, index=rng)


def timedelta_seconds(t, pos):
    td = pd.to_timedelta(t)
    return "{}".format(td.total_seconds())


fmt_seconds = FuncFormatter(timedelta_seconds)
