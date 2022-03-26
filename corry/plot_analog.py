#!/bin/env python3

import sys, os, json,argparse

parser = argparse.ArgumentParser(description='Post-processing script for corryvreckan')
parser.add_argument('-f', '--file',help='Output histogram from corry', default="analog-debug.root")
parser.add_argument('-o', '--output',help='Output file path', default='cluster.root')
parser.add_argument('-p', '--print',help='Print in PDF file', default='cluster.pdf')

args = parser.parse_args()

import ROOT
from plot_util import *

args.print = args.output.replace('.root','.pdf')

ALICEStyle()
c = ROOT.TCanvas('cQA','Corry Performance Figures',1280, 800)
c.SetMargin(0.15, 0.02, 0.15, 0.02)
c.Draw()

PrintCover(c, args.print)

corryHist = ROOT.TFile(args.file)

clusterModule = "ClusteringAnalog"
analysisModule = "AnalysisDUT"
detector = "CE65_4"

dirCluster = corryHist.Get(clusterModule).Get(detector)
dirAna = corryHist.Get(analysisModule).Get(detector)

c.Clear()
hMap = dirCluster.Get("clusterPositionLocal")
hMap.Draw("colz")
c.Print(args.print, "Title:Cluster Map")

c.Clear()
hSize = dirCluster.Get("clusterSize")
hSize.GetXaxis().SetRangeUser(0,30)
hSize.Draw()
c.Print(args.print, "Title:Cluster Size")

c.Clear()
hMap = dirAna.Get("clusterMapAssoc")
hMap.Draw("colz")
c.Print(args.print, "Title:Cluster Map (associated)")

c.Clear()
hSigX = dirAna.Get("global_residuals").Get("residualsX")
hSigX.Fit("gaus","","",-50,50)
hSigX.GetXaxis().SetRangeUser(-50,50)
hSigX.Draw()
c.Print(args.print, "Title:Tracking X")


PrintCover(c, args.print, isBack=True)
corryHist.Close()
