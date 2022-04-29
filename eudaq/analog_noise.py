#!/usr/bin/env python3

import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
import argparse
import pandas as pd

parser = argparse.ArgumentParser(description='CE65 noise player')
parser.add_argument('input', help='Dump file (NEV, NX, NY, NFRAME)')
parser.add_argument('-s', '--single', help='Display single event', default=False, action='store_true')
parser.add_argument('-d', '--debug', help='Store results', default=False, action='store_true')

args = parser.parse_args()

evdata = np.load(args.input)

NX, NY, N_FRAME= 64, 32, 8

PX, PY = 10, 10

baseline_long = []
for ev in tqdm(evdata):
  #plt.plot(ev[PX][PY])
  baseline = []
  baseline_long += list(ev[PX][PY])
  for ix in range(NX):
    for iy in range(NY):
      baseline.append( np.average(ev[ix][iy]) )
  if(args.single):
    plt.plot(baseline)
    plt.title('Average baseline of pixels (scan by X direction)')
    plt.xlabel('Pixel ID')
    plt.ylabel('Raw Amp. (ADCu)')
    plt.show()

N_WINDOW_AVG = 10
dfBaseline = pd.DataFrame(baseline_long)
avg = dfBaseline.rolling(window=N_FRAME*N_WINDOW_AVG).mean()
plt.plot(baseline_long, 'k-', label='Baseline')
plt.plot(avg, 'r-', label=f'Running Avg. ({N_WINDOW_AVG} events)')
plt.title(f'Baseline of pixels ({PX},{PY})')
plt.xlabel('Time / Frame ID')
plt.ylabel('Raw Amp. (ADCu)')
plt.legend(loc='upper left')
plt.show()
if(args.debug):
  np.save('ce65_noise-debug', baseline_long)