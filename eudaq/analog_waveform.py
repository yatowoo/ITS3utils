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
plt.title('APTS signal readout')
def DrawFrame(frdata, norm=True):
  baseline = int(frdata[0])
  if(norm):
    plt.plot(range(200),[int(x)-baseline for x in frdata])
  else:
    plt.plot(range(200),frdata)

# TODO: Use enum/bitmap instead
checkBaselineReference = False
checkOverflow = False
checkSeedOnly = False

checkCluster = True
checkChargeSharing = True
checkClusterSampling  =True

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
            if(checkBaselineReference and sigFr < BASELINE_REF):
              DrawFrame(frdata)
          if(sigVal > maxSignal):
            maxSignal, maxFrame = sigVal, sigFr
            seedX, seedY = ix, iy
            frMax = frdata
          if(checkOverflow and sigVal > SIGNAL_MAX):
            DrawFrame(frdata, norm=False)
    if(checkSeedOnly):
      DrawFrame(frMax)
    if(checkCluster):
      samplingPoints = []
      for ix in range(NX):
          for iy in range(NY):
            frdata = [int(x) for x in ev[ix][iy]]
            sigVal, sigFr = signal(frdata)
            if(sigVal > SIGNAL_CUT):
              samplingPoints.append(sigFr)
            DrawFrame(frdata)
      if(checkChargeSharing and nFiredPixel < 2):
        plt.clf()
        continue
      samplingSync = (sum([abs(x-maxFrame) for x in samplingPoints]) == 0)
      if(checkClusterSampling and samplingSync):
        plt.clf()
        continue
      else:
        plt.text(40, -0.5 * maxSignal, 'Min. frames: \n' + '\n'.join([str(x) for x in samplingPoints]) + '\nSeed: ' + str(maxFrame))
      plt.title('APTS waveforms in same cluster')
      plt.show()
plt.show()