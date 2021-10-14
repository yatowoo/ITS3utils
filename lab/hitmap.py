#!/usr/bin/env python3

import argparse
import numpy as np
from matplotlib import pyplot as plt
from alpidedaqboard import decoder
from tqdm import tqdm

parser=argparse.ArgumentParser(description='The hitmap scanner')
parser.add_argument('rawdata', metavar='FILENAME',help='raw data file to be processed')
parser.add_argument('--bins' ,'-b',type=int,choices=[1,2,4,8,16,32],help='bin size',default=1)
parser.add_argument('--max' ,'-M',type=int,help='color scale limit')
args=parser.parse_args()

hm=np.zeros((512,1024))

outfilename=args.rawdata.split("/")[-1].split(".")[0]

# https://stackoverflow.com/a/8090605
def rebin(a, shape):
    sh = shape[0],a.shape[0]//shape[0],shape[1],a.shape[1]//shape[1]
    return a.reshape(sh).mean(-1).mean(1)

with open(args.rawdata,'rb') as f:
     d=f.read()
     i=0
     pbar=tqdm(total=len(d))
     while i<len(d):
         hits,iev,tev,j=decoder.decode_event(d,i)
         for x,y in hits:
             hm[y,x]+=1
         pbar.update(j-i)
         i=j
         
plt.imshow(hm)
plt.colorbar()
#plt.clim((0,1000))
plt.xlabel('column')
plt.ylabel('row')
plt.savefig('%s-hitmap.png'%(outfilename))
plt.clf()

hm_draw = hm.ravel()
n, bins, patches = plt.hist(hm_draw,bins=100)
plt.xlabel('hits in pixel')
plt.ylabel('count')
plt.savefig('%s-rate.png'%(outfilename))

print('Average hitcount: %.2f +/- %.2f (based on %d hits)'%(np.mean(hm),np.std(hm),np.sum(hm)))

