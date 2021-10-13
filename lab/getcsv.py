#!/usr/bin/env python3

import argparse
import csv


def getcsv(inputfile,outputfile):

        #assignment of DAQ boards to chips, valid as of 11.03.2021 for REF planes of large µITS3 Setup
        #chipToDaqMap = [{'DAQ':'DAQ-0009092509591126', 'chipID': '608519W07R10'}, {'DAQ':'DAQ-000909250959381A', 'chipID': '700789W10R7'}, {'DAQ':'DAQ-00090611004E2A11', 'chipID': 'T968879W04R05'},{'DAQ':'DAQ-00090611004E160A', 'chipID': '700789W10R6'},{'DAQ':'DAQ-0009060A02441C27', 'chipID':'700789W10R16'},{'DAQ':'DAQ-00090611004E160B', 'chipID':'700789W10R4'}]

        chipToDaqMap = [{'DAQ':'DAQ-00090611004E0B0D', 'chipID': 'T968879W23TC3'}]

        rows=[]

        with open(inputfile,'r') as f:
                for line in f:
                        if "DAQ:" in line:
                                entry=[]
                                daq=line[4:].strip(' ').strip('\n')
                                entry.append(daq)
                                rowPrinted=False
                                for i in range(len(chipToDaqMap)):
                                        if chipToDaqMap[i]['DAQ']==daq:
                                                entry.append(chipToDaqMap[i]['chipID'])
                        if "VCASN:" in line:
                                entry.append(line[6:].strip(' ').strip('\n'))
                        if "ITHR:" in line:
                                entry.append(line[5:].strip(' ').strip('\n'))
                        if "Threshold:" in line:
                                thrLine=line[10:].strip(' ').strip('\n').split('+/-')
                                thr=thrLine[0].strip(' ')
                                thrErr=thrLine[1][:5].strip(' ')
                                entry.append(thr)
                                entry.append(thrErr)
                        if len(entry)==6 and rowPrinted==False:
                                rows.append(entry)
                                rowPrinted=True

        with open(outputfile, 'a+', newline='') as csvfile:
                csv_writer = csv.writer(csvfile, delimiter=',')
                csv_writer.writerow(['DAQ','chipID','VCASN','ITHR','Threshold','Threshold Uncertainty'])
                for j in range(len(rows)):
                        csv_writer.writerow(rows[j])




if __name__ == "__main__":
    parser=argparse.ArgumentParser(description='Sorts output text file of analyse_thr.sh into .csv')
    parser.add_argument('-i','--input', type=str, metavar='INPUTFILE', help='input file')
    parser.add_argument('-o','--output', type=str, metavar='OUTPUTFILE',help='name of output file')
    args=parser.parse_args()

    outfile = args.output if args.output is not None else 'output.csv'

    getcsv(inputfile=args.input,outputfile=outfile)
