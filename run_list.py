#!/bin/env python3

import os, time
import argparse

# INPUT
parser=argparse.ArgumentParser(description='Run list generator',formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--start', '-s',default='run284150051_210715160244.raw', help='Set start run with raw file name')
parser.add_argument('--data', '-d',default='/media/T71/SPSjuly2021/uITS3g1/Vbb0/', help='Data directory')
parser.add_argument('--run', '-r',default='/home/llautner/eudaq2/user/ITS3/misc/', help='Path for configuration files')
parser.add_argument('--csv',default='/home/llautner/tmp/uITS3g1_0V_scan_round2.csv', help='Threshold scan file')
parser.add_argument('--nothr', default=False, action='store_true', help='Disable threshold extrapolation')
args=parser.parse_args()

RUN_DIR = args.run
RUN_START = args.start
DATA_DIR = args.data

RUN_SIZE = 430000000 # Check smaller run by file SIZE of raw data

# Result from Threshold scan (uITS3g1_0V_scan_round2.csv / uITS3g1_3V_scan_round2.csv)
import config_thr
if(not args.nothr):
  config_thr.InitScanData(args.csv)

# Run list
runList = []
RUN_START_TIME = os.path.getmtime(DATA_DIR + RUN_START)
RUN_NOW_TIME = time.time() - 60
for fileName in next(os.walk(DATA_DIR))[2]:
  filePath = DATA_DIR + '/' + fileName
  fileTime = os.path.getmtime(filePath)
  if(fileTime >= RUN_START_TIME and fileTime < RUN_NOW_TIME):
    runInfo ={}
    runInfo['no'] = fileName
    with open(filePath, errors='ignore') as f:
      f.readline()
      f.readline()
      configFile = f.readline().split()[2]
      runInfo['configPath'] = RUN_DIR + configFile
      runInfo['config'] = os.path.basename(configFile)
      if(len(runInfo['config']) < 31):
        runInfo['config'] += ' '
    if(args.nothr):
      runInfo['thr'] = 100.
    else:
      thrRes = config_thr.ConfigThreshold(runInfo['configPath'])
      runInfo['thr'] = sum(thrRes['thr']) / len(thrRes['thr'])
    runInfo['end'] = time.strftime('%H:%M', time.localtime(fileTime))
    runInfo['size'] = os.path.getsize(filePath)
    if(runInfo['size'] < RUN_SIZE):
      runInfo['comment'] = 'Smaller RUN, check raw data'
    else:
      runInfo['comment'] = ''
    runList.append(runInfo)

# CONFIG

# Output for eLogEntry
print('Run Number                   |  THRe  | Config                          | End   | Nevents | Size/MB | Comments')
for run in sorted(runList,key=(lambda x:x['no'])):
  print('%s| %3d e- | %s | %s |   300k  | %7.0f | %s' % (run['no'], int(run['thr']), run['config'], run['end'], run['size']/1e6, run['comment']))

# END
