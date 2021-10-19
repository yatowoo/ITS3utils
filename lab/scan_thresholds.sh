#!/bin/bash -
#DAQS=$(alpide-daq-program -l | grep -o DAQ-.* | cut -f1 -d' ') # scan all connected DAQ boards
DAQS=('DAQ-00090611004E150B')

declare -A vcasn_sets
vcasn_sets=(
["DAQ-00090611004E150B"]="108 109 110"
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

#DAQS=('DAQ-00090425010F0C31')   #specifiy DAQ board serial numbers manually
#VCASN=(110)
#VCASN=(54 55 56 57 58 60)
#VCASN=(55)
ITHR=(60)
chipid=16
dvmax=20
vclip=60 #60 for Vbb=-3V, 0 for Vbb=0V
vcasn2add=12
#Note, below no absolute path!
ALPIDE_DAQ=/home/pi/llautner/alpide-daq-software/
outputdir=./output/
workingdir=$(pwd)

echo "Output directory: " $outputdir
echo "VCASN2 minus VCASN: " $vcasn2add
echo "Chip ID: " $chipid
echo "VClip: " $vclip
echo "dvmax: " $dvmax
echo "DAQ-board IDs: " $DAQS

for daq in ${DAQS[@]}; do
    VCASN=${vcasn_sets[$daq]};
    for vcasn in $VCASN; do
        vcasn2=$(($vcasn+$vcasn2add))
        for ithr in "${ITHR[@]}"; do
            echo "DAQ:    " $daq
            echo "VCASN:  " $vcasn
            echo "VCASN2: " $vcasn2
            echo "ITHR:   " $ithr
	    mkdir -p $outputdir/output_$daq/
            fname=thrscan-$daq-$vclip-$ithr-$vcasn
	    echo $outputdir/output_$daq/$fname.raw
	    $ALPIDE_DAQ/scans/thrscan.py -s $daq -v $vcasn -w $vcasn2 -i $ithr --dvmax=$dvmax --vclip=$vclip --chipid=$chipid --output=$outputdir/output_$daq/$fname.raw --params=$outputdir/output_$daq/$fname.json
	    cd $outputdir/output_$daq/
	    unset DISPLAY
	    $ALPIDE_DAQ/analyses/thrscanana.py $fname.{raw,json} 2>&1 >/dev/null &
	    cd $workingdir 
	done
    done
done

