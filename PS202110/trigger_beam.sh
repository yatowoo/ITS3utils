#!/bin/sh -
export TRIGGER_PORT=/dev/serial/by-id/usb-CERN_ITS3_Trigger_Board_210512_1140-if01-port0 

function trigger-init(){
  set -x
  ~/trigger/software/settrg.py -p $TRIGGER_PORT --trg='trg0&trg1&dt_trg>10000 &dt_veto>10000 & !bsy' --veto='ntrg>0'
  ~/trigger/software/mcp4728.py -p $TRIGGER_PORT -a 96 -c0 -v1
  ~/trigger/software/mcp4728.py -p $TRIGGER_PORT -a 96 -c1 -v1
  ~/trigger/software/mcp4728.py -p $TRIGGER_PORT -a 96 -c2 -v1
  ~/trigger/software/mcp4728.py -p $TRIGGER_PORT -a 96 -c3 -v1
  ~/trigger/software/mcp4728.py -p $TRIGGER_PORT -a 97 -c0 -v1
  ~/trigger/software/mcp4728.py -p $TRIGGER_PORT -a 97 -c1 -v1
  ~/trigger/software/mcp4728.py -p $TRIGGER_PORT -a 97 -c2 -v1
  ~/trigger/software/mcp4728.py -p $TRIGGER_PORT -a 97 -c3 -v1
  set +x
}
function trigger-mon(){
  ~/trigger/software/readtrgincnts.py -p $TRIGGER_PORT --dt 1 -n 10000 $@
}
alias trigmon-ext='trigger-mon xRxx'
alias trigmon-veto='trigger-mon RxRL'
alias trigmon-coin='trigger-mon RxRx'
function trigger-ext(){
  echo '[-] Trigger condition : trg2'
  ~/trigger/software/settrg.py -p $TRIGGER_PORT --trg='trg2&dt_trg>10000 &dt_veto>10000 & !bsy' --veto='ntrg>0'
  trigmon-ext
}
function trigger-veto(){
  echo '[-] Trigger condition : trg1 AND trg3 AND !trg0'
  ~/trigger/software/settrg.py -p $TRIGGER_PORT --trg='trg1&trg3&!trg0&dt_trg>10000 &dt_veto>10000 & !bsy' --veto='ntrg>0'
  trigmon-veto
}
function trigger-coin(){
  echo '[-] Trigger condition : trg1 AND trg3'
  ~/trigger/software/settrg.py -p $TRIGGER_PORT --trg='trg1&trg3&dt_trg>10000 &dt_veto>10000 & !bsy' --veto='ntrg>0'
  trigmon-coin
}
