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
parser.add_argument('-p','--pixel', help='Store Pixel ID', type=str, default="10,10")

args = parser.parse_args()

evdata = np.load(args.input)

NX, NY, N_FRAME= 64, 32, 8
SUBMATRIX_N         = 3
SUBMATRIX_EDGE = [21, 42, 64]
SUBMATRIX_CUT       = [1500, 1800, 500]
SUBMATRIX_TAG    = ['AC amp.', 'DC amp.', 'SF']

colorset = ['k','b','r']

def getSub(px, py):
  for i,edge in enumerate(SUBMATRIX_EDGE):
    if(px < edge):
      return i
  return -1

if(args.pixel.find(",") != -1):
  PX = int( args.pixel.split(',')[0])
  PY = int( args.pixel.split(',')[1])
else:
  pixelID = int(args.pixel)
  PX = int(pixelID / NY)
  PY = pixelID - PX * NY

baseline_long = []
for ev in tqdm(evdata):
  #plt.plot(ev[PX][PY])
  baseline = []
  pxID = []
  for i in range(SUBMATRIX_N):
    pxID.append([])
    baseline.append([])
  if(not args.single):
    baseline_long += list(ev[PX][PY])
  for ix in range(NX):
    for iy in range(NY):
      iSub = getSub(ix,iy)
      pxID[iSub].append(iy + ix * NY)
      baseline[iSub].append( np.average(ev[ix][iy]) )
  if(args.single):
    fig, pads = plt.subplots(1, 2, figsize=(10,4),gridspec_kw={'width_ratios': [2, 1]})
    for i in range(SUBMATRIX_N):
      pads[0].scatter(pxID[i],baseline[i],c=colorset[i], label=SUBMATRIX_TAG[i])
      _ = pads[1].hist(baseline[i],color=colorset[i],alpha=0.7)
    plt.suptitle('Average baseline of pixels (scan by X direction)')
    pads[0].legend(loc='upper left')
    pads[0].set_xlabel('Pixel ID')
    pads[0].set_ylabel('Raw Amp. (ADCu)')
    pads[1].set_xlabel('Raw Amp. (ADCu)')
    pads[1].set_ylabel('Number of pixels')
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