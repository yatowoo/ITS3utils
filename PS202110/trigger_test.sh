#!/bin/sh -

set -x
TRIGGER_PORT=/dev/serial/by-id/usb-CERN_ITS3_Trigger_Board_210512_1140-if01-port0 
~/trigger/software/settrg.py -p $TRIGGER_PORT --trg='trg0|trg1|trg3' --veto='ntrg>0'
~/trigger/software/mcp4728.py -p $TRIGGER_PORT -a 96 -c1 -v0.1
~/trigger/software/mcp4728.py -p $TRIGGER_PORT -a 96 -c0 -v1
~/trigger/software/mcp4728.py -p $TRIGGER_PORT -a 96 -c2 -v0.1
~/trigger/software/mcp4728.py -p $TRIGGER_PORT -a 97 -c3 -v1
~/trigger/software/mcp4728.py -p $TRIGGER_PORT -a 96 -c2 -v1
~/trigger/software/mcp4728.py -p $TRIGGER_PORT -a 96 -c3 -v0.1
~/trigger/software/mcp4728.py -p $TRIGGER_PORT -a 97 -c2 -v1
~/trigger/software/mcp4728.py -p $TRIGGER_PORT -a 97 -c3 -v0.1
~/trigger/software/readtrgincnts.py -p $TRIGGER_PORT xxxR --dt 1 -n 10000
set +x
