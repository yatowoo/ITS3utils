#!/bin/bash

# ||----- Description -----||
# This script is for testing ALPIDE chips.
# It just helps to automatically run scans provided in https://gitlab.cern.ch/alice-its3-wp3/alpide-daq-software 
# Authors: B.Ulukutlu, E.Chizzali, L.Lautner
# ToDo: Add options (--runall, --analysis=1/0, --power, --analog, --digital, --fifo, --dac, --threshold, --fakehit, --vbb=0/-3)

#For output on terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;94m'
ORANGE='\033[0;33m'
RST='\033[0m'
BLINK='\033[5m'
BOLD='\033[1m'

# ||----- Configuration -----||
# set ChipNAME_tests to the name of the chip you are testing
ChipNAME_tests=backbias-3
# alpideanafolder should be set to the absolute path where the alpide-daq-software is installed
alpdideanafolder=/home/pi/daq_software/alpide-daq-software/alpide-daq-software


# ||----- Settings -----||
# Feel free to adjust all these parameters to suit your testing needs.

# Getting the serial number of the DAQ boards to be tested
DAQS=$(alpide-daq-program -l | grep -o DAQ-.* | cut -f1 -d' ') # scan all connected DAQ boards
#DAQS=('DAQ-00090611004E0B0D')   #specify DAQ board serial numbers manually

chipid=0 #chipid=16 for unbent chips, chipid=0 or 1 for bent chips
dvmax=50 #largest voltage step to be injected
vclip=60 #ALPIDE VCLIP DAC setting: 60 for Vbb=-3V, 0 for Vbb=0V
vcasn=110 #ALPIDE VCASN DAC setting: 110 for Vbb=-3V, 60 for 0V
ithr=51 #ALPIDE ITHR DAC setting: fixed to 51 for the moment
vcasn2add=12 #VCASN2 is always set to be 12 larger than VCASN
vcasn2=$(($vcasn+$vcasn2add)) #ALPIDE VCASN2 DAC setting
echo $vcasn2

# ||----- Program DAQ boards -----||
# This will program all DAQ-boards connected to the PC
# Set the directories of fpga-v1.0.0.bit and fx3.img if you don't have them in /alpide-daq-software
echo -e "${ORANGE}${BOLD}Programming DAQ boards${RST}"
alpide-daq-program --all --fpga $alpdideanafolder/fpga-v1.0.0.bit --fx3 $alpdideanafolder/fx3.img

# ||----- Create new directory -----||
# This will create a new folder with the set chip name and save all test results inside
#You can change workingdir here if you don't want to save in current directory. But note, no absolute path!
workingdir=$(pwd)
echo "${ORANGE}${BOLD}Creating new directory for test results${RST}"
mkdir $workingdir/$ChipNAME_tests
cd $workingdir/$ChipNAME_tests

# ||----- Run scans -----||
# <<-- Power test -->>
# Power test is used to see if the chip can be turned on, and how much analog/digital current is flowing
echo "${ORANGE}${BOLD}Running Power test${RST}"
power -s $DAQS > power.txt
echo -e "${BLUE}${BOLD}Power test complete!${RST}"

# <<-- Analog test -->>
# Analog test gives a large analog pulse to see which pixels don't respond. (These are dead pixels)
# It also looks for pixels who respond when there is no pulse (These are noisy pixels)
echo "${ORANGE}${BOLD}Running Analog test${RST}"
#numpix=$(analog -s $DAQS -c $chipid | awk -v FS="(Total|pixel)" '{print $2}')
/home/pi/TEST/alpide-daq-software/scans/analog -s $DAQS -c $chipid -v $vcasn -w $vcasn2 -i $ithr -x $vclip > ANfil.txt
echo -e "${BLUE}${BOLD}Analog test complete!${RST}"
#[[ $numpix -eq 0 ]] && echo "Chip broken" && exit 666
num=$(ls -1q ana*.raw | wc -l)
[[ $num -eq 1 ]] && echo "Start analog analysis." || echo echo "Multiple analog*.raw file. Newest one is being analyzed." 
analogfile=$(ls -t analog*.raw | head -1)
echo "Filename: $analogfile" 
$alpideanafolder/analyses/analogana $analogfile  > analog.txt
echo -e "Analog Analysis complete!"

# <<-- Digital test -->>
# Digital test does ...?
echo "${ORANGE}${BOLD}Running Digital test${RST}"
digital -s $DAQS -c $chipid --dctrl > digital_measurement.txt
echo -e "${BLUE}${BOLD}Digital test complete!${RST}"
numdig=$(ls -1q digi*.raw | wc -l)
[[ $num -eq 1 ]] && echo "Start digital analysis." || echo "Multiple digital*.raw file. Newest one is being analyzed."
digifileraw=$(ls -t digi*.raw | head -1)
digifiledat=$(ls -t digi*.dat | head -1)
echo "Filename: $digifileraw and $digifiledat"
$alpideanafolder/analyses/digitalana $digifiler > digital.txt
echo -e "Digital Analysis complete!"

# <<-- FIFO test -->>
# FIFO test writes some test data to the First In First Out Memory unit on the chip and reads back what was written.
# If these match than the fifo unit is working
echo "${ORANGE}${BOLD}Running Fifo test${RST}"
fifo -s $DAQS -c $chipid > fifo.txt
echo -e "${BLUE}${BOLD}Fifo test complete!${RST}"

# <<-- DAC test -->>
# DAC test checks the digital-to-analog and analod-to-digital conversion of various on the chip (could be inaccurate description?)
echo "${ORANGE}${BOLD}Running Dac test${RST}"
dac -s $DAQS -c $chipid --via-daq-board 1 > dac_exp.txt
echo -e "${BLUE}${BOLD}Dac test complete${RST}!"
numdac=$(ls -1q dac*.txt | wc -l)
[[ $num -eq 1 ]] && echo "Start Dac analysis." || echo "Multiple dac*.raw file. Newest one is being analyzed."
dacfile=$(ls -t dacscan*.txt | head -1)
$alpideanafolder/analyses/dacana $dacfile > dac.txt
echo -e "Dac Analysis complete!"

# <<-- Threshold scans -->>
# The threshold scan is used to find the threshold DAC pulse which is needed to trigger pixels.
# If the DAC value is small this means that a small pulse is enough to trigger.
# The VCASN, VCASN2 and ITHR settings change the effective amplitude of the sent pulse and thus can change the threshold value.
# The aim with these tests is to find settings which lead to a average threshold value of 10 DAC values on the chip.
# -- Run scans --
# Here the thrscan is run multiple times with different vcasn and ithr values.
VCASN_list=(106 107 108 109)
ITHR_list=(51)
#configure which/how many rows will be scanned on the chip
first_row=0 #first row to be scanned
row_iteration_step = 64; #step size for row numbers to be scanned: =1 scans entire chip, =512 scans only one row

echo "${ORANGE}${BOLD}Running Threshold scans${RST}"
for daq in ${DAQS[@]}; do
    for vcasn_i in "${VCASN_list[@]}"; do
        vcasn2_i=$(($vcasn+$vcasn2add))
        for ithr_i in "${ITHR_list[@]}"; do
            echo "DAQ:    " $daq
            echo "VCASN:  " $vcasn_i
            echo "VCASN2: " $vcasn2_i
            echo "ITHR:   " $ithr_i
            fname=thrscan-$daq-$vclip-$ithr-$vcasn
			echo $workingdir$fname.raw
            awk 'BEGIN {for (i=$first_row;i<512;i+=$row_iteration_step) print "-r " i}' | xargs thrscan -s $daq -v $vcasn_i -w $vcasn2_i -i $ithr_i --dvmax=$dvmax --vclip=$vclip --chipid=$chipid --dctrl --output=$workingdir$fname.raw --params=$workingdir$fname.json
		done
    done
done
echo -e "${BLUE}${BOLD}Threshold scans complete${RST}!"

# -- Run analysis on measured thresholds --
echo -e "${ORANGE}${BOLD}Running threshold analysis${RST}!"
for daq in ${DAQS[@]}; do
    for vcasn_i in "${VCASN_list[@]}"; do
        for ithr_i in "${ITHR_list[@]}"; do
            echo "DAQ:    " $daq
            echo "VCASN:  " $vcasn_i
            echo "ITHR:   " $ithr_i
            thrscanana $workingdir/thrscan-$daq-$vclip-$ithr_i-$vcasn_i.{raw,json} >> threshold_scan_output.txt
        done
    done
done
# The output of the analysis is saved in the file threshold_scan_output.txt

#ToDo: get the VCASN, VCASN2 and ITHR values for which average threshold is 10 DAC values

# <<-- Fake hit rate scan -->>
# ToDo make fake hit rate scan and hitmap analysis once the proper settings can be obtained from the threshold scan
