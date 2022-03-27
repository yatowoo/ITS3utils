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
c = ROOT.TCanvas('cQA','Corry Performance Figures',1280, 800)
c.SetMargin(0.15, 0.02, 0.15, 0.1)
c.Draw()

def DrawHist(htmp, title="", option=""):
  c.Clear()
  htmp.Draw(option)
  if(title == ""):
    title = htmp.GetTitle()
  c.Print(args.print, "Title:"+title)

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
hSize = dirCluster.Get("clusterCharge")
hSize.Rebin(int(100. / hSize.GetBinWidth(1)))
hSize.GetXaxis().SetRangeUser(-1000,20000)
hSize.Draw()
c.Print(args.print, "Title:Cluster charge")

c.Clear()
hSize = dirCluster.Get("clusterSeedCharge")
hSize.Rebin(int(100. / hSize.GetBinWidth(1)))
hSize.GetXaxis().SetRangeUser(0,10000)
hSize.Draw()
c.Print(args.print, "Title:Cluster seed charge")

c.Clear()
hSize = dirCluster.Get("clusterNeighborsCharge")
hSize.Rebin(int(100. / hSize.GetBinWidth(1)))
hSize.GetXaxis().SetRangeUser(-5000,5000)
hSize.Draw()
c.Print(args.print, "Title:Cluster neighbors charge")

hSize = dirCluster.Get("clusterNeighborsChargeSum")
hSize.Rebin(int(100. / hSize.GetBinWidth(1)))
hSize.GetXaxis().SetRangeUser(-5000,10000)
DrawHist(hSize, "Cluster neighbors charge")

hRatio = dirCluster.Get("clusterChargeRatio")
hRatio.GetXaxis().SetRangeUser(0,10)
DrawHist(hRatio, "Cluster charge ratio", "colz")

hSize = dirCluster.Get("clusterSeedSNR")
hSize.Rebin(int(0.5 / hSize.GetBinWidth(1)))
hSize.GetXaxis().SetRangeUser(0,100)
DrawHist(hSize, "Cluster neighbors charge")

hSize = dirCluster.Get("clusterNeighborsSNR")
hSize.GetXaxis().SetRangeUser(-10,10)
DrawHist(hSize, "Cluster neighbors charge")

hMap = dirCluster.Get("clusterSeed_Neighbors")
DrawHist(hMap, "clusterSeed_Neighbors", "colz")

hMap = dirCluster.Get("clusterSeed_NeighborsSNR")
DrawHist(hMap, "clusterSeed_NeighborsSNR", "colz")

hMap = dirCluster.Get("clusterSeed_NeighborsSum")
DrawHist(hMap, "clusterSeed_NeighborsSum", "colz")

hMap = dirCluster.Get("clusterSeed_Cluster")
DrawHist(hMap, "clusterSeed_Cluster", "colz")

hMap = dirCluster.Get("clusterSeedSNR_Cluster")
DrawHist(hMap, "clusterSeedSNR_Cluster", "colz")

c.Clear()
hMap = dirAna.Get("clusterMapAssoc")
hMap.Draw("colz")
c.Print(args.print, "Title:Cluster Map (associated)")

c.Clear()
hSigX = dirAna.Get("global_residuals").Get("residualsX")
hSigX.Rebin(int(1. / hSigX.GetBinWidth(1)))
hSigX.Fit("gaus","","",-50,50)
hSigX.GetXaxis().SetRangeUser(-50,50)
hSigX.Draw()
c.Print(args.print, "Title:Tracking X")

c.Clear()
hSigX = dirAna.Get("global_residuals").Get("residualsY")
hSigX.Rebin(int(1. / hSigX.GetBinWidth(1)))
hSigX.Fit("gaus","","",-50,50)
hSigX.GetXaxis().SetRangeUser(-50,50)
hSigX.Draw()
c.Print(args.print, "Title:Tracking Y")


PrintCover(c, args.print, isBack=True)
corryHist.Close()
