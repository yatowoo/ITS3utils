#!/bin/env python3

import config_thr
from scipy import interpolate
import matplotlib.pyplot as plt
import copy

THR_FIXED=[5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 35, 40]

config_thr.THR_DATA = {}
config_thr.InitScanData('uITS3g2/dut_0VBB.csv')
config_thr.ThresholdForConfig(THR_FIXED)

configData = config_thr.THR_DATA['DUT0'][50]
plt.plot(configData['vcasn'], configData['threshold'],'ro',ms=5)
plt.plot(configData['vcasn_config'], THR_FIXED,'gs',ms=3)
plt.plot(configData['vcasn_fit'], configData['thr_fit'])
plt.show()
