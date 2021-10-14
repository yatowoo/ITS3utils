#!/usr/bin/env python3

from alpidedaqboard import alpidedaqboard
import argparse
import datetime
import json
from time import sleep
from tqdm import tqdm
from alpidedaqboard import decoder
import os


ROWS_AT_A_TIME=4
now=datetime.datetime.now()

parser=argparse.ArgumentParser(description='The mighty threshold scanner')
parser.add_argument('--serial' ,'-s',help='serial number of the DAQ board')
parser.add_argument('--chipid' ,'-c',type=int,help='Chip ID (default: 0x10)',default=0x10)
parser.add_argument('--vresetd',     type=int,help='ALPIDE VRESETD DAC setting (default: 147)',default=147)
parser.add_argument('--vhi' ,type=int,help='VPULSEH (default: 170)',default=170)
parser.add_argument('--vlo' ,type=int,help='VPULSEL (default: 100)',default=100)
parser.add_argument('--dctrl'  ,     action='store_true',help='use readout via DCTRL')
parser.add_argument('--params' ,'-p',help='name of file to which settings are written')
parser.add_argument('--path',help='path', default='.' )
parser.add_argument('--vcasn', '-v',type=int, help='vcasn', default=110)
parser.add_argument('--vcasn2', '-w',type=int, help='vcasn2', default=122)
parser.add_argument('--vclip', '-x',type=int, help='vclip', default=60)
parser.add_argument('--ithr', '-i',type=int, help='ithr', default=51)
args=parser.parse_args()


if args.serial:
    fname='analog-%s-%s'%(args.serial,now.strftime('%Y%m%d_%H%M%S'))
else:
    fname='analog-%s'%(now.strftime('%Y%m%d_%H%M%S'))


if not args.params: args.params=fname+'.json'

if args.path != '.':  #creating new directory
    try:
        os.mkdir(args.path)
    except OSError:
        print ("Creation of the directory %s failed" %args.path)

with open('%s/%s'%(args.path,args.params),'w') as f:
    f.write(json.dumps(vars(args)))


try:
    daq=alpidedaqboard.ALPIDEDAQBoard(args.serial)
except ValueError as e:
    print(e)
    raise SystemExit(-1)

# Well, power has a too bad connotation sometimes.
daq.power_on()
sleep(0.1) # let it settle
iaa,idd,status=daq.power_status()
print('IAA = %5.2f mA'%iaa)
print('IDD = %5.2f mA'%idd)
if status:
    print('LDOs: ON')
else:
    print('LDOs: OFF... too bad!')
    raise SystemExit(1)


#just in case we got up on the wrong side of the fw...
daq.fw_reset()
daq.alpide_cmd_issue(0xD2) # GRST for ALPIDE
# now for monitoring, also start clean
daq.fw_clear_monitoring()
daq.alpide_cmd_issue(0xE4) # PRST

daq.alpide_reg_write(0x0004,0x0060,chipid=args.chipid) # disable busy monitoring, analog test pulse, enable test strobe
daq.alpide_reg_write(0x0005,   200,chipid=args.chipid) # strobe length
daq.alpide_reg_write(0x0007,     0,chipid=args.chipid) # strobe->pulse delay
daq.alpide_reg_write(0x0008,   400,chipid=args.chipid) # pulse duration
daq.alpide_reg_write(0x0010,0x0030,chipid=args.chipid) # initial token, SDR, disable manchester, previous token == self!!!
daq.alpide_reg_write(0x0001,0x000D,chipid=args.chipid) # normal readout, TRG mode
daq.alpide_cmd_issue(0x63) # RORST (needed!!!)

if args.dctrl:
    daq.alpide_reg_write(0x0001,0x020D,chipid=args.chipid) # normal readout, TRG mode, CMU RDO
    daq.rdoctrl.delay_set.write(1000) # when to start reading (@80MHz, i.e. at least strobe-time x2 + sth.)
    daq.rdoctrl.chipid.write(args.chipid)
    daq.rdoctrl.ctrl.write(1) # enable DCTRL RDO
    daq.rdomux.ctrl.write(2) # select DCTRL RDO
else:
    daq.alpide_reg_write(0x0001,0x000D,chipid=args.chipid) # normal readout, TRG mode
    daq.rdopar.ctrl.write(1) # enable parallel port RDO
    daq.rdomux.ctrl.write(1) # select parallel port RDO
    daq.xonxoff.ctrl.write(1) # enable XON XOFF

daq.trg.ctrl.write(0b1110) # master mode,  mask ext trg, mask ext busy, do not force forced busy
daq.trgseq.dt_set.write(4000) # 50 us
daq.trg.opcode.write(0x78) # PULSE OPCODE

#daq.alpide_reg_write(0x0605,args.vhi,chipid=args.chipid) # VPULSEH
#daq.alpide_reg_write(0x0606,args.vlo,chipid=args.chipid) # VPULSEL
#daq.alpide_reg_write(0x0602,args.vresetd,chipid=args.chipid) # VRESETD
daq.alpide_reg_write(0x0604,args.vcasn,chipid=args.chipid) # VRESETD
daq.alpide_reg_write(0x0607,args.vcasn2,chipid=args.chipid) # VRESETD
daq.alpide_reg_write(0x0608,args.vclip,chipid=args.chipid) # VRESETD
daq.alpide_reg_write(0x060E,args.ithr,chipid=args.chipid) # VRESETD

	
total=0
print('Starting analog test...')
try:
    with open('%s/%s'%(args.path,fname+'.raw'),'wb') as datafile:
       for y in tqdm(range(0,512,ROWS_AT_A_TIME),desc="Overall progress"):
           daq.alpide_pixel_pulsing_all(False,chipid=args.chipid)
           daq.alpide_pixel_mask_all(True,chipid=args.chipid)
           for yy in range(y,y+ROWS_AT_A_TIME):
               daq.alpide_pixel_mask_row(yy,False,chipid=args.chipid)
               daq.alpide_pixel_pulsing_row(yy,True,chipid=args.chipid)
           daq.trgseq.start.issue()
           ev=daq.event_read()
           datafile.write(ev)
           hits,iev,tev,j=decoder.decode_event(ev,0)
           total+=len(hits)
except KeyboardInterrupt:
    print('Test interrupted!')

print("Total %d pixel responses"%(total))
#daq.power_off()


