#!/bin/bash
#Forward the std output to an external file
#./analyse_thr.sh > output.txt
DAQS=$(alpide-daq-program -l | grep -o DAQ-.* | cut -f1 -d' ')
#DAQS=('DAQ-00090425010F0C31')
VCASN=(110)
#VCASN=(54 55 56 57 58 60)
#VCASN=(55)
ITHR=(51)
vclip=60 #60 for Vbb=-3V, 0 for Vbb=0V
ALPIDE_DAQ=/home/pi/llautner/alpide-daq-software-latest/
inputdir=./output/

for daq in ${DAQS[@]}; do
    for vcasn in "${VCASN[@]}"; do
        for ithr in "${ITHR[@]}"; do
            echo "DAQ:    " $daq
            echo "VCASN:  " $vcasn
            echo "ITHR:   " $ithr
            $ALPIDE_DAQ/analyses/thrscanana.py $inputdir/output_$daq/thrscan-$daq-$vclip-$ithr-$vcasn.{raw,json}
        done
    done
done
