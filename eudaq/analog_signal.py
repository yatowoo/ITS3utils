#!/usr/bin/env python3

import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
import argparse
import pandas as pd

parser = argparse.ArgumentParser(description='CE65 signal player')
parser.add_argument('input', help='Dump file (NEV, NX, NY, NFRAME)')
parser.add_argument('-s', '--single', help='Display single event', default=False, action='store_true')
parser.add_argument('-d', '--debug', help='Store results', default=False, action='store_true')
parser.add_argument('-e', '--nev', default=1000000,
                    type=int, help='N events to read')

args = parser.parse_args()

evdata = np.load(args.input)

NX, NY, N_FRAME= 64, 32, 8

PX, PY = 10, 10

SUBMATRIX_N         = 3
SUBMATRIX_EDGE = [21, 42, 64]
SUBMATRIX_CUT       = [1500, 1800, 500]
SUBMATRIX_TAG    = ['AC amp.', 'DC amp.', 'SF']

def getSub(px, py):
  for i,edge in enumerate(SUBMATRIX_EDGE):
    if(px < edge):
      return i
  return -1
def getCut(px, py):
  try:
    return SUBMATRIX_CUT[getSub(px, py)]
  except Exception:
    return 0

def UpdatePlot(title=''):
  if(title != ''):
    plt.suptitle(title)
  else:
    plt.suptitle('Analogue waveform display')
  plt.tight_layout()
  plt.show()

fig, pads = plt.subplots(1, SUBMATRIX_N, figsize=(15,4))
args.nev = min(len(evdata), args.nev)
for iev in tqdm(range(args.nev)):
  ev = evdata[iev]
  #plt.plot(ev[PX][PY])
  if(args.single):
    fig.clf()
    fig, pads = plt.subplots(1, SUBMATRIX_N, figsize=(15,4))
  for pad, tag in zip(pads, SUBMATRIX_TAG):
    pad.set_title(f'Sub-matrix ({tag})')
    pad.set_xlabel('Frame No.')
    pad.set_ylabel('ADCu')
  for ix in range(NX):
    for iy in range(NY):
      fr = [x - ev[ix][iy][0] for x in ev[ix][iy]]
      if(abs(fr[-1]-fr[0]) > getCut(ix,iy)):
        drawOpt = 'r-'
        if(not args.single):
          pads[getSub(ix,iy)].plot(fr)
      else:
        drawOpt = 'k-'
      if(args.single):
        _ = pads[getSub(ix,iy)].plot(fr, drawOpt)
  if(args.single):
    UpdatePlot('Analogue waveform (all pixels)')

UpdatePlot('Signal waveform (all events)')