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

for ev in tqdm(evdata):
    # Find max. pixel
    maxSignal = 0
    seedX, seedY = 0, 0
    frMax = None
    for ix in range(NX):
        for iy in range(NY):
          frdata = [int(x) for x in ev[ix][iy]]
          sigVal, sigFr = signal(frdata)
          #if(sigVal > SIGNAL_CUT and sigFr < 30):
          if(sigVal > maxSignal):
            maxSignal = sigVal
            seedX, seedY = ix, iy
            frMax = frdata
          if(sigVal > SIGNAL_MAX):
            DrawFrame(frdata, norm=False)

plt.show()