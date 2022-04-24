import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
fileDump = 'scint-trig-signal200.out.npy'
evdata = np.load(fileDump)
NX, NY, N_FRAME= 4, 4, 200
SIGNAL_CUT = 200
SIGNAL_MAX = 6000
FIXED_TRIG_FRAME = 100
N_BASELINE = 10
BASELINE_REF = 30
def baseline(frdata):
    #sumRegion = sum(frdata[0:N_BASELINE])
    #return (sumRegion / N_BASELINE)
    return frdata[0]
def signal(frdata):
    # Negative signal
    val =  -(min(frdata) - baseline(frdata))
    return (val, np.argmin(frdata))

plt.figure(1)
plt.plot(range(200))
plt.show(block=False)
plt.clf()

checkBaselineReference = (1<<0)
checkOverflow = (1<<1)
checkSeedOnly = (1<<2)

checkCluster = (1<<3)
checkChargeSharing = (1<<4) | checkCluster
checkClusterSampling  = (1<<5) | checkChargeSharing

plotSingle = (1<<6)

#PLOT_SELECTION = 0b111000
PLOT_SELECTION = checkBaselineReference | plotSingle

saveFigIndex = 0
def UpdatePlot(title=''):
  if(title != ''):
    plt.title(title)
  else:
    plt.title('APTS readout - waveform display')
  plt.draw()
  cmd = input("Next => ")
  if(cmd.lower().find('a') != -1):
    global PLOT_SELECTION
    PLOT_SELECTION ^= plotSingle
  if(cmd.lower().find('s') != -1):
    global saveFigIndex
    plt.savefig(fileDump.split('.')[0] + f'_{saveFigIndex}.png')
    saveFigIndex += 1
  if(cmd.lower().find('q') != -1):
    exit()
  plt.clf()

def DrawFrame(frdata, norm=True):
  baseline = int(frdata[0])
  if(norm):
    plt.plot([int(x)-baseline for x in frdata])
  else:
    plt.plot(frdata)
  if(PLOT_SELECTION & plotSingle):
    UpdatePlot()

for ev in tqdm(evdata):
    # Find max. pixel
    maxSignal, maxFrame = 0, 0
    seedX, seedY = 0, 0
    frMax = None
    nFiredPixel = 0
    for ix in range(NX):
        for iy in range(NY):
          frdata = [int(x) for x in ev[ix][iy]]
          sigVal, sigFr = signal(frdata)
          if(sigVal > SIGNAL_CUT):
            nFiredPixel += 1
            if(PLOT_SELECTION & checkBaselineReference
             and sigFr < BASELINE_REF):
              DrawFrame(frdata)
          if(sigVal > maxSignal):
            maxSignal, maxFrame = sigVal, sigFr
            seedX, seedY = ix, iy
            frMax = frdata
          if(PLOT_SELECTION & checkOverflow and sigVal > SIGNAL_MAX):
            DrawFrame(frdata, norm=False)
    if(PLOT_SELECTION & checkSeedOnly):
      DrawFrame(frMax)
    if(PLOT_SELECTION & checkCluster):
      samplingPoints = []
      for ix in range(NX):
          for iy in range(NY):
            frdata = [int(x) for x in ev[ix][iy]]
            sigVal, sigFr = signal(frdata)
            if(sigVal > SIGNAL_CUT):
              samplingPoints.append(sigFr)
            DrawFrame(frdata)
      if(PLOT_SELECTION & checkChargeSharing and nFiredPixel < 2):
        plt.clf()
        continue
      samplingSync = (sum([abs(x-maxFrame) for x in samplingPoints]) == 0)
      if(PLOT_SELECTION & checkClusterSampling and samplingSync):
        plt.clf()
        continue
      else:
        plt.text(40, -0.5 * maxSignal, 'Min. frames: \n' + '\n'.join([str(x) for x in samplingPoints]) + '\nSeed: ' + str(maxFrame))
      UpdatePlot('APTS waveforms in same cluster')

UpdatePlot()