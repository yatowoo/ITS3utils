import matplotlib.pyplot as plt
import numpy as np
evdata = np.load('test.out.npy')
frdata = evdata[-1][1][1]
baseline = int(frdata[0])
plt.figure(1)
plt.title('APTS signal readout')
plt.plot(range(200),[int(x)-baseline for x in frdata])
plt.show()