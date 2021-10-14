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
ALPIDE_DAQ=/home/pi/alpide-daq-software
DAQS=$(alpide-daq-program -l | grep -o DAQ-.* | cut -f1 -d' ') # scan all connected DAQ boards
#DAQS=('DAQ-00090611004E0B0D')   #specifiy DAQ board serial numbers manually
chipid=16
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
echo "Running Power test - all ALPIDE"
for DAQ in $DAQS;
do
  cd $workingdir
  mkdir -p output_$DAQ
  cd output_$DAQ
  echo "Running Power test - "$DAQ;
  $ALPIDE_DAQ/scans/power-on.py -s $DAQ | tee power_$DAQ.txt;
  echo -e "Power test complete!"
  echo "Running Analog test - "$DAQ;
  $ALPIDE_DAQ/scans/analog.py -s $DAQS -c $chipid -v $vcasn -w $vcasn2 -x $vclip -i $ithr --dctrl | tee analog_$DAQ.txt
  echo -e "Analog test complete!"
  #[[ $numpix -eq 0 ]] && echo "Chip broken" && exit 666
  num=$(ls -1q ana*.raw | wc -l)
  [[ $num -eq 1 ]] && echo "Start analog analysis." || echo "Multiple analog*.raw file. Newest one is being analyzed."
  analogfile=$(ls -t analog*.raw | head -1)
  echo "Filename: $analogfile"
  $ALPIDE_DAQ/analyses/analogana.py $analogfile > analog.txt
  echo -e "Analog Analysis complete!"
  echo "Running Digital test"
  $ALPIDE_DAQ/scans/digital.py -s $DAQS -c $chipid --dctrl > digital_measurment.txt
  echo -e "Digital test complete!"
  numdig=$(ls -1q digi*.raw | wc -l)
  [[ $num -eq 1 ]] && echo "Start digital analysis." || echo "Multiple digital*.raw file. Newest one is being analyzed."
  digifileraw=$(ls -t digi*.raw | head -1)
  digifiledat=$(ls -t digi*.dat | head -1)
  echo "Filename: $digifileraw and $digifiledat"
  $ALPIDE_DAQ/analyses/digitalana.py $digifileraw $digifiledat > digital.txt
  echo -e "Digital Analysis complete!"
  echo "Running Fifo test"
  $ALPIDE_DAQ/scans/fifo.py -s $DAQS -c $chipid > fifo.txt
  echo -e "Fifo test complete!"
  echo "Running Dac test"
  $ALPIDE_DAQ/scans/dac.py -s $DAQS -c $chipid --via-daq-board 1 > dac.txt
  echo -e "Dac test complete!"
  numdac=$(ls -1q dac*.txt | wc -l)
  [[ $num -eq 1 ]] && echo "Start Dac analysis." || echo "Multiple dac*.raw file. Newest one is being analyzed."
  dacfile=$(ls -t dac*.txt | head -1)
  $ALPIDE_DAQ/analyses/dacana.py $dacfile > dac.txt
  echo -e "Dac Analysis complete!";
done







