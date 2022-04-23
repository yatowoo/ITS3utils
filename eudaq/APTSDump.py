#!/usr/bin/env python3

import argparse
import pyeudaq
import mlr1daqboard
import numpy as np
from tqdm import tqdm
from ROOT import TH2F, TFile

parser=argparse.ArgumentParser(description='APTS data dumper')
parser.add_argument('input',help='EUDAQ raw file')
parser.add_argument('output',help='numpy file to dump events to')
parser.add_argument('--apts-id',default='APTS_0',help='ID of APTS in data (default: APTS_0)')
parser.add_argument('-e','--nev',default=1e6,type=int,help='N events to read')
parser.add_argument('-d','--dump',default=False,help='save np.array into file', action='store_true')
parser.add_argument('-v','--debug',default=False,help='Print debug info.', action='store_true')

args=parser.parse_args()

fr=pyeudaq.FileReader('native',args.input)

# DEBUG
if(args.nev < 0):
    args.nev = 1e6 # Reset to default

fRoot = TFile('h2trig.root','RECREATE')
hTrigger = TH2F('h2trig','Sampling point vs pedestal;ADCu (Min. - Baseline);Frame. No.;#pixels', 1000, -1000.5, 9000-0.5, 200, -0.5, 200-0.5)
hTrigger.SetDrawOption('colz')
hTriggerConv = TH2F('h2trig_conv','Sampling point vs pedestal (min. frame of seed);ADCu (Min. - Baseline);Frame. No.;#pixels', 1000, -1000.5, 9000-0.5, 200, -0.5, 200-0.5)
hTriggerConv.SetDrawOption('colz')
hTriggerSeed = TH2F('h2trig_seed','Sampling point vs pedestal (seed);ADCu (Min. - Baseline);Frame. No.;#pixels', 1000, -1000.5, 9000-0.5, 200, -0.5, 200-0.5)
hTriggerSeed.SetDrawOption('colz')
# np.array - (4,4,nframes)
NX, NY, N_FRAME= 4, 4, 200
SIGNAL_CUT = 200
FIXED_TRIG_FRAME = 100
N_BASELINE = 10
def baseline(frdata):
    #sumRegion = sum(frdata[0:N_BASELINE])
    #return (sumRegion / N_BASELINE)
    return frdata[0]
def signal(frdata):
    # Negative signal
    val =  -(min(frdata) - baseline(frdata))
    return (val, np.argmin(frdata))
# Input:
# Return: 
def eventCut(evdata):
    # ADCu = val - baseline [1st frame]
    eventPass = False
    sigMax, frMax = 0, 0
    for ix in range(NX):
        for iy in range(NY):
            sigVal, sigFr = signal([int(x) for x in evdata[ix][iy]])
            hTrigger.Fill(sigVal, sigFr)
            if(sigVal > sigMax):
                sigMax = sigVal
                frMax = sigFr
            if(sigVal > SIGNAL_CUT):
                eventPass = True
                # DEBUG
                if(args.debug):
                    print(f'[+] Signal found : ({ix},{iy},{sigFr}) - ADC value = {sigVal}')
    hTriggerSeed.Fill(sigMax,frMax)
    for ix in range(NX):
        for iy in range(NY):
            chargeInConverter = -(evdata[ix][iy][frMax] - evdata[ix][iy][0])
            hTriggerConv.Fill(chargeInConverter, frMax)
    return eventPass

evds =[]
trgs =[]
evns =[]
ts   =[]
nEvent = 1000
for iev in tqdm(range(args.nev)):
    ev=fr.GetNextEvent()
    if ev is None: break
    sevs=ev.GetSubEvents()
    if sevs is None: break
    for sev in sevs:
        if sev.GetDescription()==args.apts_id:
            evd,t=mlr1daqboard.decode_apts_event(sev.GetBlock(0),decode_timestamps=True)
            # DEBUG
            if(eventCut(evd) and args.dump):
                ts.append(t)
                evds.append(evd)
                trgs.append(sev.GetTriggerN())
                evns.append(sev.GetEventN())
                np.save(args.output,evds)
                if(args.debug):
                    exit()
            break
        
if(args.dump):
    np.save(args.output,evds)
fRoot.cd()
htmp = hTrigger.ProjectionX()
htmp.Write()
htmp = hTriggerConv.ProjectionX()
htmp.Write()
htmp = hTriggerSeed.ProjectionX()
htmp.Write()
hTrigger.Write()
hTriggerConv.Write()
hTriggerSeed.Write()
fRoot.Close()
exit()

# TODO: what about the first event which seems to have one ADC extra
evds=evds[1:]
trgs=trgs[1:]
evns=evns[1:]
ts  =ts  [1:]

dout=np.array(list(zip(ts,trgs,evns,evds)),dtype=[('time',np.uint64),('trgn',np.uint64),('evn',np.uint64),('adcs',np.uint16,evds[0].shape)])
np.save(args.output,dout)
