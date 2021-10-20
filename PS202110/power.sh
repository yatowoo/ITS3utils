#!/bin/bash -
if [ -z $RUN_DIR ];then
  echo '[x] RUN_DIR not found. Set to ~/eudaq2/user/ITS3/misc as default'
  export RUN_DIR=~/eudaq2/user/ITS3/misc
else
  echo '[-] ITS3 running director : '$RUN_DIR
fi

if [ -f $RUN_DIR/../python/HAMEG.py ];then
  HAMEG_CONTORL=$RUN_DIR/../python/HAMEG.py
else
  HAMEG_CONTORL=$RUN_DIR/../python/HMP4040.py;
fi

function power-refs(){
  python3 $RUN_DIR/../python/HAMEG.py -p /dev/serial/by-id/usb-HAMEG_HAMEG_HO720_023899455-if00-port0 $@
  echo "Description  :   REF DAQ power      REF Vbb      TRIG POWER     TRIG POWER"
}

function power-usb(){
  python3 $RUN_DIR/../python/HAMEG.py -p /dev/serial/by-id/usb-HAMEG_HAMEG_HO720_023516024-if00-port0 $@
  echo "Description  :      CE65 HV       CE65 PWELL      APTS DAQ       USB hub "
}

function power-ce65(){
  power-usb $@
}

function power-apts(){
  python3 $RUN_DIR/../python/HAMEG.py -p /dev/serial/by-id/usb-HAMEG_HAMEG_HO720_021028153-if00-port0 $@
  echo "Description  :       B5 SUB         B5 PWELL        B2 SUB       B2 PWELL"
}

function power-dpts(){
  python3 $RUN_DIR/../python/HAMEG.py -p /dev/serial/by-id/usb-HAMEG_HAMEG_HO720_019603994-if00-port0 $@
  echo "Description  :        DAQ              DUT          TRIGGER"
}
