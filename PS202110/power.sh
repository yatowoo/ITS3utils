#!/bin/bash -

if [ -f $RUN_DIR/../python/HAMEG.py ];then
  export HAMEG_CONTROL=$RUN_DIR/../python/HAMEG.py
else
  export HAMEG_CONTROL=$RUN_DIR/../python/HMP4040.py;
fi

function power-refs(){
  python3 $HAMEG_CONTROL -p /dev/serial/by-id/usb-HAMEG_HAMEG_HO720_023899455-if00-port0 $@
  echo "Description  :   REF DAQ power      REF Vbb      TRIG POWER     TRIG POWER"
}

function power-usb(){
  python3 $HAMEG_CONTROL -p /dev/serial/by-id/usb-HAMEG_HAMEG_HO720_023516024-if00-port0 $@
  echo "Description  :      CE65 HV       CE65 PWELL      APTS DAQ       USB hub "
}

function power-ce65(){
  power-usb $@
}

function power-apts(){
  python3 $HAMEG_CONTROL -p /dev/serial/by-id/usb-HAMEG_HAMEG_HO720_021028153-if00-port0 $@
  echo "Description  :       B5 SUB         B5 PWELL        B2 SUB       B2 PWELL"
}

function power-dpts(){
  python3 $HAMEG_CONTROL -p /dev/serial/by-id/usb-HAMEG_HAMEG_HO720_019603994-if00-port0 $@
  echo "Description  :        DAQ              DUT          TRIGGER"
}
