#!/usr/bin/env python3

import argparse
import pyeudaq
import mlr1daqboard
import numpy as np
from tqdm import tqdm
from ROOT import TH2F, TFile

parser = argparse.ArgumentParser(description='CE65 data dumper')
parser.add_argument('input', help='EUDAQ raw file')
parser.add_argument(
    '-o', '--output', help='numpy file to dump events to', default='ce65_dump')
parser.add_argument('--dut-id', dest='dut_id', default='CE65Raw',
                    help='ID of CE65 in data (default: CE65Raw)')
parser.add_argument('-e', '--nev', default=1000000,
                    type=int, help='N events to read')
parser.add_argument('-d', '--dump', default=False,
                    help='save np.array into file', action='store_true')
parser.add_argument('-v', '--debug', default=False,
                    help='Print debug info.', action='store_true')

args = parser.parse_args()

fr = pyeudaq.FileReader('native', args.input)

# DEBUG
if(args.nev < 0):
    args.nev = int(1e6)  # Reset to default

# np.array - (4,4,nframes)
NX, NY, N_FRAME = 64, 32, 9
SIGNAL_CUT = 200
FIXED_TRIG_FRAME = 100
N_BASELINE = 10


def baseline(frdata):
    #sumRegion = sum(frdata[0:N_BASELINE])
    # return (sumRegion / N_BASELINE)
    return frdata[0]


def signal(frdata):
    # Negative signal
    val = -(min(frdata) - baseline(frdata))
    return (val, np.argmin(frdata))


def eventCut(evdata):
    # ADCu = val - baseline [1st frame]
    eventPass = False
    sigMax, frMax = 0, 0
    for ix in range(NX):
        for iy in range(NY):
            eventPass = True
    return eventPass


def decode_event(raw):
    evdata = np.zeros((NX, NY, N_FRAME))
    for ifr in range(raw.GetNumBlock()):
        rawfr = raw.GetBlock(ifr)
        assert(len(rawfr) == 2*NX*NY)
        for ix in range(NX):
            for iy in range(NY):
                iPx = iy + ix * NY
                # unit8_t *2 => short/unit16
                evdata[ix][iy][ifr] = int(
                    rawfr[2*iPx+1] << 8) + int(rawfr[2*iPx])
    return evdata


evds = []

nEvent = 1000
for iev in tqdm(range(args.nev)):
    ev = fr.GetNextEvent()
    if ev is None:
        break
    sevs = ev.GetSubEvents()
    if sevs is None:
        break
    for sev in sevs:
        if sev.GetDescription() == args.dut_id:
            evdata = decode_event(sev)
            # DEBUG
            if(eventCut(evdata)):
                evds.append(evdata)
                if(args.debug):
                    np.save(args.output, evdata)
                    exit()
            break

if(args.dump):
    np.save(args.output, evds)

print(f'[+] CE65 event found : {len(evds)}')
