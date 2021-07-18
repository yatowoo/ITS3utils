#!/bin/env python3
 
import json, copy
with open('Setup.json') as f:
  SETUP_DB = json.load(f)

KEY_VALUE_FORMATTER = '%-16s = %s'
def print_section(headers):
  for name in headers:
    print('[%s]' % name)
    for k, v in SETUP_DB[name].items():
      print(KEY_VALUE_FORMATTER % (k, v))
    print()

print_section(['RunControl', 'Producer.POWER', 'Producer.PTH'])

# Chip config.
chipName = []
for chipID in SETUP_DB['general']['Setup']:
  chipConf = SETUP_DB['CHIPS'][chipID]
  header = chipConf['name']
  chipName.append(header)
  confData = SETUP_DB[header] = copy.deepcopy(SETUP_DB['general']['ALPIDE'])
  for k in chipConf.keys():
    if(k == 'name'):
      continue
    confData[k] = chipConf[k]
print_section(chipName)

print_section(['DataCollector.dc'])
