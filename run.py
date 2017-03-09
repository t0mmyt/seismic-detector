# -*- coding: utf-8 -*-
import obspy
import matplotlib.pyplot as plt
import seaborn
import logging
#from logging import debug
from detector import Detector


if __name__=="__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    seaborn.set()
    o = "/srv/seismic_raw/2011.239/2011.239.00.00.00.0000.YW.NAB2..HHZ.D.SAC"
    
    s = obspy.read(o)
    d = Detector(s[0].data, s[0].meta.sampling_rate)
    d.bandpass(5, 7)
    fig = plt.figure(figsize=(12, 6), dpi=100)
    ax1 = fig.add_subplot(111)
    for x in d.detect(1000, 20000, nstds=1):
        ax1.axvline(x[0], ymin=0.5, ymax=1, color='red', lw=1)
    for x in d.detect(1000, 15000, nstds=1):
        ax1.axvline(x[0], ymin=0, ymax=0.5, color='green', lw=1)
    ax1.plot(d.stream)    