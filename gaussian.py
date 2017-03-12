#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 12 14:06:55 2017

@author: tom
"""
import logging
from logging import debug
import matplotlib.pyplot as plt
import numpy as np
import seaborn
from math import exp, inf, floor
from scipy.integrate import quad


def g(x, b=0, c2=0.2):
    """
    Guassian distribution function
    """
    return exp(-(x - b)**2 / (2 * c2))


def int_g(x1, x2):
    """
    Integral of g
    """
    return quad(g, x1, x2)

def breakpoint(xx, yy, a=4, digits=5):
    assert len(xx) == len(yy), "Arrays were not equal length"
    total_area = np.trapz(yy, xx)
    debug("Total area: {}".format(total_area))
    desired_area = round(total_area / a, digits)
    debug("Desired area: {}".format(desired_area))
    
    last_divide = cur_x = floor(len(xx) / 2)
    
    while last_divide > 1:
        last_divide /= 2
        area = round(np.trapz(yy[:cur_x], yy[:cur_x]), digits)
        debug("Last divide, cur_x, area: {}\t{}\t{}".format(last_divide, cur_x, area))
        if area == desired_area:
            return xx[cur_x], cur_x
        elif area < desired_area:
            cur_x = floor(cur_x + last_divide)
        elif area > desired_area:
            cur_x = floor(cur_x - last_divide)
    return xx[cur_x], cur_x
            

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
                        
xx = np.linspace(-2, 2, 10000)
yy = np.array([g(x) for x in xx])

seaborn.set()

#plt.plot(xx, yy)
#print(np.trapz(yy, xx))
#print(int_g(-inf, inf))
print(breakpoint(xx, yy))



