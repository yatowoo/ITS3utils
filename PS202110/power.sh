#!/bin/bash -
function power-refs(){
  python3 $RUN_DIR/../python/HMP4040.py -p /dev/serial/by-id/usb-HAMEG_HAMEG_HO720_023899455-if00-port0 $@
  echo "Description  :   REF DAQ power      REF Vbb      TRIG POWER     TRIG POWER"
}

function power-usb(){
  python3 $RUN_DIR/../python/HMP4040.py -p /dev/serial/by-id/usb-HAMEG_HAMEG_HO720_023516024-if00-port0 $@
  echo "Description  :      CE65 HV       CE65 PWELL      APTS DAQ       USB hub "
}

function power-ce65(){
  power-usb $@
}

function power-apts(){
  python3 $RUN_DIR/../python/HMP4040.py -p /dev/serial/by-id/usb-HAMEG_HAMEG_HO720_021028153-if00-port0 $@
  echo "Description  :       B5 SUB         B5 PWELL        B2 SUB       B2 PWELL"
}
