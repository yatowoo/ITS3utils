#!/bin/bash
#Forward the std output to an external file
#./analyse_thr.sh > output.txt
DAQS=$(alpide-daq-program -l | grep -o DAQ-.* | cut -f1 -d' ')

declare -A vcasn_sets
vcasn_sets=(
["DAQ-00090611004E160A"]="108 109 110 111 112"
["DAQ-000909250959131E"]="108 109 110 111 112"
["DAQ-00090611004E2A11"]="104 105 106 107 108"
["DAQ-000904250114120A"]="105 106 107"
["DAQ-0009060A02441C27"]="105 106 107 109 110 111 112"
["DAQ-00090611004E0B0D"]="105 106 108 109 110 111 112"
["DAQ-000909250959071E"]="105 105 107 108 109 111 112"
["DAQ-000904250102072C"]="102 103 104 105 106"
["DAQ-00090425010F0C31"]="108 109 110 111"
["DAQ-000909250959381A"]="107 108 109 110 111")

#DAQS=('DAQ-00090425010F0C31')
#VCASN=(110)
#VCASN=(54 55 56 57 58 60)
#VCASN=(55)
ITHR=(60)
vclip=60 #60 for Vbb=-3V, 0 for Vbb=0V
ALPIDE_DAQ=/home/pi/llautner/alpide-daq-software/
inputdir=./output/
workingdir=$(pwd)

for daq in ${DAQS[@]}; do
    VCASN=${vcasn_sets[$daq]};
    for vcasn in $VCASN; do 
        for ithr in "${ITHR[@]}"; do
            echo "DAQ:    " $daq
            echo "VCASN:  " $vcasn
            echo "ITHR:   " $ithr
	    cd $inputdir/output_$daq/
	    unset DISPLAY
            $ALPIDE_DAQ/analyses/thrscanana.py thrscan-$daq-$vclip-$ithr-$vcasn.{raw,json}
	    cd $workingdir 
        done
    done
done
