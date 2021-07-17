#!/bin/env python3

import csv
from scipy import interpolate
import numpy as np
import os

THR_DATA = {}
def InitScanData(csvFile):
  with open(csvFile) as f:
    reader = csv.DictReader(f)
    for row in reader:
      chipID = row['chipID']
      if(not THR_DATA.get(chipID)):
        THR_DATA[chipID] = {}
      ithr = int(row['ITHR'])
      if(not THR_DATA[chipID].get(ithr)):
        THR_DATA[chipID][ithr] = {}
        THR_DATA[chipID][ithr]['vcasn'] = []
        THR_DATA[chipID][ithr]['threshold'] = []
      if(row['Threshold'] == 'nan'):
        continue
      THR_DATA[chipID][ithr]['vcasn'].append(int(row['VCASN']))
      THR_DATA[chipID][ithr]['threshold'].append(float(row['Threshold']) )
  # Create spline interpolation
  for chip in THR_DATA.keys():
    for ithr in THR_DATA[chip].keys():
      THR_DATA[chip][ithr]['fit'] = interpolate.splrep(THR_DATA[chip][ithr]['vcasn'], THR_DATA[chip][ithr]['threshold'], s=0)

def ConfigThreshold(confPath):
  result = {}
  # VCASN settings in config. file
  THR_DATA['DUT0']['confVCASN'] = 19
  if(THR_DATA.get('DUT1')):
    THR_DATA['DUT1']['confVCASN'] = 33
  if(THR_DATA.get('DUT2')):
    THR_DATA['DUT2']['confVCASN'] = 47
  if(THR_DATA.get('DUT3')):
    THR_DATA['DUT3']['confVCASN'] = 61
  if(THR_DATA.get('DUT4')):
    THR_DATA['DUT4']['confVCASN'] = 75
  if(THR_DATA.get('DUT5')):
    THR_DATA['DUT5']['confVCASN'] = 89
  result['conf'] = confPath.split('/')[-1]
  result['thr'] = []
  with open(confPath) as f:
    confData = f.readlines()
    ithr = int(confData[18].split()[2])
    sum = 0
    for chip in sorted(THR_DATA.keys()):
      vcasn = int(confData[THR_DATA[chip]['confVCASN']].split()[2])
      thr = 10 * float(interpolate.splev(vcasn, THR_DATA[chip][ithr]['fit'], der=0))
      result['thr'].append(thr)
  return result

def ThresholdForConfig(thrList):
  for chip in THR_DATA.keys():
    print(chip)
    for ithr in THR_DATA[chip].keys():
      print(ithr, end='\t')
      THR_DATA[chip][ithr]['vcasn_config'] = []
      x = list(range(20,100,1))
      THR_DATA[chip][ithr]['vcasn_fit'] = x
      y = interpolate.splev(x, THR_DATA[chip][ithr]['fit'], der=0)
      THR_DATA[chip][ithr]['thr_fit'] = y
      for thr in thrList:
        yToFind = np.array(y) - thr
        try:
          newSpl = interpolate.CubicSpline(x,yToFind)
          THR_DATA[chip][ithr]['vcasn_config'].append(newSpl.roots()[0])
          print('%.0f' % newSpl.roots(), end=',')
        except:
          print(0,end=',')
      print()


if __name__ == "__main__":
  import argparse

  # INPUT - DEBUG (TODO: argparse)
  parser=argparse.ArgumentParser(description='Threshold calculator',formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('--csv',default='uITS3g1_0V_scan_round2.csv', help='Threshold scan file')
  parser.add_argument('--config',default='/home/llautner/eudaq2/user/ITS3/misc/uITS3g1_conf_0V_ithr_60/', help='Configuration file')
  args=parser.parse_args()

  InitScanData(args.csv)

  def keyFile(name):
    return int(name.split('-')[1].split('.')[0])

  confDir = args.config
  print('Configuration File \t-> Threshold/e-\tAvg.\t',end='')
  for chip in sorted(THR_DATA.keys()):
    print(chip,end='\t')
  print()
  for fileName in sorted(next(os.walk(confDir))[2], key=keyFile):
    if(not fileName.endswith('.conf')):
      continue
    thrRes = ConfigThreshold(confDir + '/' + fileName)
    print(fileName + '\t\t%d\t' % int(sum(thrRes['thr'])/len(thrRes['thr'])), end='')
    for val in thrRes['thr']:
      print('%3.1f' % val,end='\t')
    print()

  
