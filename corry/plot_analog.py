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
ROOT.gStyle.SetOptTitle(1)
ROOT.gStyle.SetOptStat(1)
global c
c = ROOT.TCanvas('cQA','Corry Performance Figures',2560, 1440)
c.SetMargin(0.15, 0.02, 0.15, 0.1)
c.Draw()

c.Clear()
c.Divide(4,4)
global padIndex
padIndex = 0

def DrawHist(htmp, title="", option="", optStat=True):
  ROOT.gStyle.SetOptStat(optStat)
  global padIndex
  padIndex = padIndex + 1
  c.cd(padIndex)
  print("[+] DEBUG - Pad " + str(padIndex))
  htmp.Draw(option)
  if(title == ""):
    title = htmp.GetTitle()
  if(padIndex == 16):
    c.Print(args.print, "Title:"+title)
    c.Clear()
    padIndex = 0

PrintCover(c, args.print)

corryHist = ROOT.TFile(args.file)

clusterModule = "ClusteringAnalog"
analysisModule = "AnalysisDUT"
detector = "CE65_4"

dirCluster = corryHist.Get(clusterModule).Get(detector)
dirAna = corryHist.Get(analysisModule).Get(detector)

hMap = dirCluster.Get("clusterPositionLocal")
DrawHist(hMap, "Cluster neighbors charge","colz")

hSize = dirCluster.Get("clusterSize")
hSize.GetXaxis().SetRangeUser(0,30)
DrawHist(hSize, "clusterSize")

hSize = dirCluster.Get("clusterCharge")
hSize.Rebin(int(100. / hSize.GetBinWidth(1)))
hSize.GetXaxis().SetRangeUser(-5000,20000)
DrawHist(hSize, "clusterSize")


hSize = dirCluster.Get("clusterSeedCharge")
hSize.Rebin(int(100. / hSize.GetBinWidth(1)))
hSize.GetXaxis().SetRangeUser(0,12000)
DrawHist(hSize, "clusterSize")

hSize = dirCluster.Get("clusterNeighborsCharge")
hSize.Rebin(int(100. / hSize.GetBinWidth(1)))
hSize.GetXaxis().SetRangeUser(-5000,5000)
DrawHist(hSize, "clusterSize")

hSize = dirCluster.Get("clusterNeighborsChargeSum")
hSize.Rebin(int(100. / hSize.GetBinWidth(1)))
hSize.GetXaxis().SetRangeUser(-5000,10000)
DrawHist(hSize, "Cluster neighbors charge")

hRatio = dirCluster.Get("clusterChargeRatio")
hRatio.GetXaxis().SetRangeUser(0,10)
hRatio.GetYaxis().SetRangeUser(0,1.1)
DrawHist(hRatio, "Cluster charge ratio", "colz", False)

hSize = dirCluster.Get("clusterSeedSNR")
hSize.Rebin(int(0.5 / hSize.GetBinWidth(1)))
hSize.GetXaxis().SetRangeUser(0,100)
DrawHist(hSize, "clusterSeedSNR")

hSize = dirCluster.Get("clusterNeighborsSNR")
hSize.GetXaxis().SetRangeUser(-10,10)
DrawHist(hSize, "clusterNeighborsSNR")

hMap = dirCluster.Get("clusterSeed_Neighbors")
hMap.GetYaxis().SetRangeUser(-4000,10000)
DrawHist(hMap, "clusterSeed_Neighbors", "colz", False)

hMap = dirCluster.Get("clusterSeed_NeighborsSNR")
DrawHist(hMap, "clusterSeed_NeighborsSNR", "colz", False)

hMap = dirCluster.Get("clusterSeed_NeighborsSum")
hMap.GetYaxis().SetRangeUser(-4000,10000)
DrawHist(hMap, "clusterSeed_NeighborsSum", "colz", False)

hMap = dirCluster.Get("clusterSeed_Cluster")
hMap.GetYaxis().SetRangeUser(-4000,10000)
DrawHist(hMap, "clusterSeed_Cluster", "colz", False)

hMap = dirCluster.Get("clusterSeedSNR_Cluster")
DrawHist(hMap, "clusterSeedSNR_Cluster", "colz", False)

hMap = dirCluster.Get("clusterChargeShape")
hMap.GetXaxis().SetRangeUser(-5,5)
DrawHist(hMap, "clusterChargeShape", "colz", False)

hMap = dirCluster.Get("clusterChargeShapeSNR")
hMap.GetXaxis().SetRangeUser(-5,5)
DrawHist(hMap, "clusterChargeShapeSNR", "colz", False)

hMap = dirCluster.Get("clusterChargeShapeRatio")
hMap.GetXaxis().SetRangeUser(-5,5)
DrawHist(hMap, "clusterChargeShapeRatio", "colz", False)

hMap = dirAna.Get("clusterMapAssoc")
DrawHist(hMap, "clusterSize", "colz")

hSigX = dirAna.Get("global_residuals").Get("residualsX")
hSigX.Rebin(int(1. / hSigX.GetBinWidth(1)))
hSigX.Fit("gaus","","",-50,50)
hSigX.GetXaxis().SetRangeUser(-50,50)
DrawHist(hSigX, "clusterSize")

hSigX = dirAna.Get("global_residuals").Get("residualsY")
hSigX.Rebin(int(1. / hSigX.GetBinWidth(1)))
hSigX.Fit("gaus","","",-50,50)
hSigX.GetXaxis().SetRangeUser(-50,50)
DrawHist(hSigX, "clusterSize")

c.Print(args.print, "Title:last")

PrintCover(c, args.print, isBack=True)
corryHist.Close()
