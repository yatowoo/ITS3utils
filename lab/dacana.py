#!/usr/bin/env python3

import argparse
import json
import numpy as np
import math
import os
import itertools


from matplotlib import pyplot as plt


DACs=[
  ('VRESETP', 1,4,0.4),
  ('VRESETD', 2,5,0.4),
  ('VCASP'  , 3,1,0.0),
  ('VCASN'  , 4,0,0.0),
  ('VPULSEH', 5,2,0.4),
  ('VPULSEL', 6,3,0.4),
  ('VCASN2' , 7,6,0.0),
  ('VCLIP'  , 8,7,0.0),
  ('VTEMP'  , 9,8,0.0),
  ('IAUX2'  ,10,1,0),
  ('IRESET' ,11,0,0),
  ('IDB'    ,12,3,0),
  ('IBIAS'  ,13,2,0),
  ('ITHR'   ,14,5,0)
]


parser=argparse.ArgumentParser(description='The mighty threshold scanner')
parser.add_argument('filename',help='Name of the file to analyse')
parser.add_argument('--path',help='Output plots path', default='.' )
parser.add_argument('--fit',help='Do fit?', default=True)
args=parser.parse_args()



sumfig=plt.figure()
plt.title('Summary plot')
plt.xlabel('DAC Setting')
plt.ylabel('ADC')
plt.xticks([0,64,128,192,255])

outfilename=args.filename.split("/")[-1].split(".")[0]

i=1
for vdac in DACs:
    try:
        inputf=open("%s"%(args.filename),'r')
    except IOError:
        print('ERROR: File %s could not be read!'%(args.filename))
        raise SystemExit(1)
    data=np.loadtxt(itertools.islice(inputf, 256*(i-1), 256*i),usecols=(1, 2))
    inputf.close()   #for now I don't know other way to read file again with loadtxt function
    
    if vdac==0.0:
        fit=np.polyfit(data[0:240,0],data[0:240,1],1)
    else:
        fit=np.polyfit(data[0:186,0],data[0:186,1],1)
        
    fit_fn=np.poly1d(fit)


    plt.figure(sumfig.number)
    plt.plot([x[0] for x in data],[y[1] for y in data])
    plt.figure()
    plt.xlabel('DAC Setting')
    plt.ylabel('ADC')
    plt.title('Scan of %s DAC'%vdac[0])
    plt.ylim(bottom=0,top=np.max(data[:,1])*1.1)
    plt.xlim(0,np.max(data[:,0]))

    plt.xticks([0,64,128,192,255])
    plt.plot([x[0] for x in data],[y[1] for y in data])
    x=np.linspace(0,255,256)
    if args.fit:
        plt.plot(x,fit_fn(x))
    plt.savefig('%s/%s-%s.png'%(args.path,outfilename,vdac[0]))
    plt.close()
    
    i+=1

     
plt.savefig('%s/%s-all.png'%(args.path,outfilename))
plt.close(sumfig)

print("done")

