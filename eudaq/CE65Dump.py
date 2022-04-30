#!/usr/bin/env python3

# Interface
import argparse, subprocess, re
# Event
import pyeudaq
import numpy as np
from tqdm import tqdm

# Constants and Options
NX, NY, N_FRAME     = 64, 32, 9
FIXED_TRIGGER_FRAME = 4
SUBMATRIX_N         = 3
SUBMATRIX_EDGE      = [21, 42, 63]
SUBMATRIX_CUT       = [1500, 1800, 500]
SIGNAL_METHOD       = ['cds', 'max', 'fix', 'fax']

# Arguments
parser = argparse.ArgumentParser(description='CE65 data dumper')
parser.add_argument('input', help='EUDAQ raw file')
parser.add_argument(
    '-o', '--output', help='numpy file to dump events (EV,NX,NY,FR)', default='ce65_dump')
parser.add_argument('--dut-id', dest='dut_id', default='CE65Raw',
                    help='ID of CE65 in data')
parser.add_argument('-e', '--nev', default=1000000,
                    type=int, help='N events to read')
parser.add_argument('-s', '--signal', default='cds',
                    type=str, choices=SIGNAL_METHOD, help='Signal extraction method')
parser.add_argument('-n', '--noise', default=False,
                    help='Noise run - no signal cuts', action='store_true')
parser.add_argument('-d', '--dump', default=False,
                    help='save np.array into file', action='store_true')
parser.add_argument('-v', '--debug', default=False,
                    help='Print debug info.', action='store_true')

args = parser.parse_args()

fr = pyeudaq.FileReader('native', args.input)

N_EVENTS_MAX = int(1e6)

def eudaqGetNEvents(rawDataPath):
  eudaqExe = 'euCliReader'
  cmd = [eudaqExe,"-i",rawDataPath,"-e", "10000000"]
  try:
    result = subprocess.run(cmd, stdout=subprocess.PIPE)
    cfg = re.findall(r'\d+',result.stdout.decode('utf-8'))
    print(f'[-] INFO - {cfg[0]} events found by {eudaqExe}')
    return int(cfg[0])
  except FileNotFoundError:
    print(f'[X] {eudaqExe} not found, set max. events {N_EVENTS_MAX}')
    return N_EVENTS_MAX

# N events
eudaq_nev = eudaqGetNEvents(args.input)
if(args.nev < 0):
  args.nev = min(eudaq_nev, N_EVENTS_MAX)
else:
  args.nev = min(args.nev, eudaq_nev)

# Define baseline for subtraction
def baseline(frdata):
  #sumRegion = sum(frdata[0:N_BASELINE])
  # return (sumRegion / N_BASELINE)
  return frdata[0]

# Signal extraction from analogue wavefrom by each pixel
def signal(frdata, opt='cds'):
  val, ifr = 0, 0
  opt = opt.lower().strip()
  # CDS (last - 1st)
  if(opt == 'cds'):
    val = frdata[-1] - frdata[0]
    ifr = len(frdata) -1
  # MAX (max - baseline)
  elif(opt == 'max'):
    ifr = np.argmax(frdata)
    val = frdata[ifr] - baseline(frdata)
  # FIX (TriggerFrame - baseline)
  elif(opt == 'fix'):
    ifr = FIXED_TRIGGER_FRAME
    val = frdata[ifr] - baseline(frdata)
  # FAX - MAX in FIXED trigger window +/- 1
  elif(opt == 'fax'):
    lower = min(0, FIXED_TRIGGER_FRAME-1)
    upper = max(len(frdata), FIXED_TRIGGER_FRAME+2)
    trigWindow = frdata[lower:upper]
    ifr = np.argmax(trigWindow) + lower
    val = frdata[ifr] - baseline(frdata)
  else:
    print(f'[X] UNKNOWN signal extraction method - {opt}')
  return (val, ifr)

def eventCut(evdata):
  # ADCu = val - baseline [1st frame]
  eventPass = False
  sigMax, frMax = 0, 0
  submatrixIdx = 0
  for ix in range(NX):
    if(ix > SUBMATRIX_EDGE[submatrixIdx]):
      submatrixIdx += 1
    for iy in range(NY):
      val, ifr = signal(list(evdata[ix][iy]), args.signal)
      if(abs(val) > SUBMATRIX_CUT[submatrixIdx]):
        eventPass = True
  return eventPass

def analog_qa(evdata):
  # Baseline
  # Noise
  # Signal
  return

def decode_event(raw):
    global N_FRAME
    nFrame = raw.GetNumBlock()
    if(nFrame != N_FRAME):
      print(f'[X] WARNING - Number of frames changes from {N_FRAME} to {nFrame}')
      N_FRAME = nFrame
    evdata = np.empty((NX, NY, N_FRAME),dtype=np.short)
    for ifr in range(nFrame):
        rawfr = raw.GetBlock(ifr)
        assert(len(rawfr) == 2*NX*NY)
        for ix in range(NX):
            for iy in range(NY):
                iPx = iy + ix * NY
                # uint8_t *2 => short
                try:
                  evdata[ix][iy][ifr] = np.short(int(rawfr[2*iPx+1]<<8) + int(rawfr[2*iPx]))
                except OverflowError: # sign flip
                  pass
    return evdata

evds = []
nEvent_DUT = 0
nEvent_Pass = 0
for iev in tqdm(range(args.nev)):
  ev = fr.GetNextEvent()
  if ev is None: break
  sevs = ev.GetSubEvents()
  if sevs is None: break
  for sev in sevs:
    if sev.GetDescription() != args.dut_id: continue
    # Process raw data from DUT sub-event
    nEvent_DUT += 1
    evdata = decode_event(sev)
    # DEBUG
    if(args.noise or eventCut(evdata)):
      nEvent_Pass += 1
      if(args.dump): evds.append(evdata)
    break

if(args.dump): np.save(args.output, evds)

print(f'[+] CE65 event found : {nEvent_DUT}')
print(f'[+] CE65 event pass cut : {nEvent_Pass}')