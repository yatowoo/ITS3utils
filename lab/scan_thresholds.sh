#!/bin/bash
DAQS=$(alpide-daq-program -l | grep -o DAQ-.* | cut -f1 -d' ') # scan all connected DAQ boards
#DAQS=('DAQ-00090425010F0C31')   #specifiy DAQ board serial numbers manually
VCASN=(102 104 106 107 108 109 110 112)
#VCASN=(54 55 56 57 58 60)
#VCASN=(55)
ITHR=(51)
chipid=0
dvmax=50
vclip=60 #60 for Vbb=-3V, 0 for Vbb=0V
vcasn2add=12
#Note, below no absolute path!
outputdir=./


echo "Output directory: " $outputdir
echo "VCASN2 minus VCASN: " $vcasn2add
echo "Chip ID: " $chipid
echo "VClip: " $vclip
echo "dvmax: " $dvmax
echo "DAQ-board IDs: " $DAQS

for daq in ${DAQS[@]}; do
    for vcasn in "${VCASN[@]}"; do
        vcasn2=$(($vcasn+$vcasn2add))
        for ithr in "${ITHR[@]}"; do
            echo "DAQ:    " $daq
            echo "VCASN:  " $vcasn
            echo "VCASN2: " $vcasn2
            echo "ITHR:   " $ithr
            fname=thrscan-$daq-$vclip-$ithr-$vcasn
	    echo $outputdir$fname.raw
            awk 'BEGIN {for (i=0;i<512;i+=32) print "-r " i}' | xargs /home/pi/alpide-software/alpide-daq-software/scans/thrscan.py -s $daq -v $vcasn -w $vcasn2 -i $ithr --dvmax=$dvmax --vclip=$vclip --chipid=$chipid --dctrl --output=$outputdir$fname.raw --params=$outputdir$fname.json
	done
    done
done

