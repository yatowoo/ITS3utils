#!/usr/bin/env python3
import csv
import matplotlib.pyplot as plt
import argparse

def main(inputfile, Nithr):

    colors=["r", "b", "g", "k", "c", "y"]
    with open(inputfile, "r") as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=",")

        i=0
        for row in csv_reader:
            vcasn=float(row["VCASN"])
            thres=float(row["Threshold"])
            ithr=float(row["ITHR"])
            print("ITHR =", ithr, "VCASN =", vcasn, "Threshold =", thres)
            ii=i%Nithr
            if i<Nithr:
                plt.plot(vcasn, thres, 'o', color=colors[ii], label="ITHR = %s"%ithr)
            else:
                plt.plot(vcasn, thres, 'o', color=colors[ii])
            i=i+1

    #plt.xlim([44, 71])
    plt.xlabel("VCASN")
    plt.ylabel("Threshold [DAC]")
    plt.legend()
    plt.show(block=False)
    plt.pause(0.001)
    input("Hit[enter] to end")
    plt.close('all')
    
if __name__ == "__main__":
    pass
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_file",
                        type=str,
                        default="ref-thr-vbb0-T968879W09R10.csv",
                        help="csv file with the thresholds, enter it")
    parser.add_argument("--Nithr",
                        type=float,
                        default=3,
                        help="number of scanned ITHR")
    args = parser.parse_args()
    main(inputfile=args.input_file, Nithr=args.Nithr)

   

    
