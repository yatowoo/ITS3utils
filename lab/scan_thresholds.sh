#!/bin/bash -
DAQS=$(alpide-daq-program -l | grep -o DAQ-.* | cut -f1 -d' ') # scan all connected DAQ boards

declare -A vcasn_sets
vcasn_sets=(
["DAQ-00090611004E160A"]="113" 
["DAQ-000909250959131E"]="112" 
["DAQ-00090611004E2A11"]="109" 
["DAQ-000904250114120A"]="106" 
["DAQ-0009060A02441C27"]="108" 
["DAQ-00090611004E0B0D"]="107" 
["DAQ-000909250959071E"]="110" 
["DAQ-000904250102072C"]="104" 
["DAQ-00090425010F0C31"]="110" 
["DAQ-000909250959381A"]="112")

#DAQS=('DAQ-00090425010F0C31')   #specifiy DAQ board serial numbers manually
#VCASN=(110)
#VCASN=(54 55 56 57 58 60)
#VCASN=(55)
ITHR=(60)
chipid=16
dvmax=50
vclip=60 #60 for Vbb=-3V, 0 for Vbb=0V
vcasn2add=12
#Note, below no absolute path!
ALPIDE_DAQ=/home/pi/llautner/alpide-daq-software-latest/
outputdir=./output/

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
	    $ALPIDE_DAQ/scans/thrscan.py -s $daq -v $vcasn -w $vcasn2 -i $ithr --dvmax=$dvmax --vclip=$vclip --chipid=$chipid --dctrl --output=$outputdir/output_$daq/$fname.raw --params=$outputdir/output_$daq/$fname.json
	done
    done
done

