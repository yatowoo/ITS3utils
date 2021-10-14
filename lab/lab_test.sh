#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
ORANGE='\033[0;33m'
RST='\033[0m'
BLINK='\033[5m'
BOLD='\033[1m'

#echo -e "${RED}${BOLD}FAILED!${RST}"

#echo -e "${ORANGE}${BOLD}WARNING!${RST}"

#echo -e "${GREEN}${BOLD}SUCCESS!${RST}"

ChipNAME_tests=C7G

DAQS=$(alpide-daq-program -l | grep -o DAQ-.* | cut -f1 -d' ') # scan all connected DAQ boards
#DAQS=('DAQ-00090611004E0B0D')   #specifiy DAQ board serial numbers manually
chipid=0
dvmax=50
vclip=60 #60 for Vbb=-3V, 0 for Vbb=0V
vcasn=110
vcasn2add=12
ithr=51

vcasn2=$(($vcasn+$vcasn2add))
#Note, below no absolute path!
workingdir=$(pwd)
#echo "Creating new folders for test results of " $ChipNAME
#mkdir $workingdir/$ChipNAME_tests

#cd $workingdir/$ChipNAME_tests
set -xv
echo "Running Power test"
/home/pi/alpide-software/alpide-daq-software/scans/power-on.py -s $DAQS > power.txt
echo -e "Power test complete!"
echo "Running Analog test"
/home/pi/alpide-software/alpide-daq-software/scans/analog.py -s $DAQS -c $chipid -v $vcasn -w $vcasn2 -x $vclip -i $ithr --dctrl
echo -e "Analog test complete!"
#[[ $numpix -eq 0 ]] && echo "Chip broken" && exit 666
num=$(ls -1q ana*.raw | wc -l)
[[ $num -eq 1 ]] && echo "Start analog analysis." || echo "Multiple analog*.raw file. Newest one is being analyzed."
analogfile=$(ls -t analog*.raw | head -1)
echo "Filename: $analogfile"
/home/pi/alpide-software/alpide-daq-software/analyses/analogana.py $analogfile > analog.txt
echo -e "Analog Analysis complete!"
echo "Running Digital test"
/home/pi/alpide-software/alpide-daq-software/scans/digital.py -s $DAQS -c $chipid --dctrl > digital_measurment.txt
echo -e "Digital test complete!"
numdig=$(ls -1q digi*.raw | wc -l)
[[ $num -eq 1 ]] && echo "Start digital analysis." || echo "Multiple digital*.raw file. Newest one is being analyzed."
digifileraw=$(ls -t digi*.raw | head -1)
digifiledat=$(ls -t digi*.dat | head -1)
echo "Filename: $digifileraw and $digifiledat"
/home/pi/alpide-software/alpide-daq-software/analyses/digitalana.py $digifileraw $digifiledat > digital.txt
echo -e "Digital Analysis complete!"
echo "Running Fifo test"
/home/pi/alpide-software/alpide-daq-software/scans/fifo.py -s $DAQS -c $chipid > fifo.txt
echo -e "Fifo test complete!"
echo "Running Dac test"
/home/pi/alpide-software/alpide-daq-software/scans/dac.py -s $DAQS -c $chipid --via-daq-board 1 > dac.txt
echo -e "Dac test complete!"
numdac=$(ls -1q dac*.txt | wc -l)
[[ $num -eq 1 ]] && echo "Start Dac analysis." || echo "Multiple dac*.raw file. Newest one is being analyzed."
dacfile=$(ls -t dac*.txt | head -1)
/home/pi/alpide-software/alpide-daq-software/analyses/dacana.py $dacfile > dac.txt
echo -e "Dac Analysis complete!"







