# -*- coding: utf-8 -*-
import obspy
from obspy import UTCDateTime
import matplotlib.pyplot as plt
import seaborn
import logging
#from logging import debug
import numpy as np
from timeit import default_timer
from seismic.detector import Detector
from seismic.frequency import Frequency


if __name__=="__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    seaborn.set()
    
#    o = "/srv/seismic_raw/2011.249/2011.249.00.00.00.0000.YW.NAB1..HHZ.D.SAC"
    o = "/srv/seismic_raw/2011.250/2011.250.00.00.00.0000.YW.NAB1..HHZ.D.SAC"
    s = obspy.read(o)
    slice = s[0].slice(
        UTCDateTime("2011-09-07T14:47:30.000000Z"),
        UTCDateTime("2011-09-07T14:48:45.000000Z")
#        UTCDateTime("2011-09-07T00:30:10.000000Z"),
#        UTCDateTime("2011-09-07T00:30:45.999999Z")
#        UTCDateTime("2011-09-07T12:35:00.000000Z"),
#        UTCDateTime("2011-09-07T12:39:59.999999Z")
#        UTCDateTime("2011-09-06T18:20:00.000000Z"),
#        UTCDateTime("2011-09-06T23:59:59.999999Z")
    )    
    d = Detector(slice.data, slice.meta.sampling_rate)
    d.bandpass(5, 10)
    start = s[0].meta.starttime

    fig = plt.figure(figsize=(12, 8), dpi=100)
    ax1 = fig.add_subplot(111)
    ax1.grid(b=False)
#    ax3 = fig.add_subplot(212)

    ax2 = ax1.twinx()
    ax2.grid(b=False)
    short = 250
    long = 15000


#    a = list(zip(*d.windows(short, long, nstds=3)))
#    sm = ax2.plot(a[0], a[3], color='red', label='Short Mean')
#    lm = ax2.plot(a[0], a[1], color='blue', label='Long Mean')
#    lsm = ax2.plot(a[0], np.add(a[1], a[2]), color='g', label='Long Mean + STD')
#    ax2.legend()
#
#    ax1.plot(d.trace, color='#aaaaff')    
#    t = default_timer()
#    for x in d.detect(short, long, nstds=3, trigger_len=2000):
#        ax1.axvline(x[0], ymin=0, ymax=1, color='green', lw=1)
#        ax1.axvline(x[1], ymin=0, ymax=1, color='red', lw=1)
#        print(x)
#    print("{:.3f}".format(default_timer() - t))
    ff = Frequency(slice.data, slice.meta.sampling_rate)
    for i in ff.find_inversions():
        print("{}".format(i))
        