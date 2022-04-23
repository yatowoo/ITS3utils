#!/bin/env python3

import sys, os, json,argparse

parser = argparse.ArgumentParser(description='Post-processing script for corryvreckan')
parser.add_argument('-f', '--file',help='Output histogram from corry', default="analog-debug.root")
parser.add_argument('-o', '--output',help='Output file path', default='cluster.root')
parser.add_argument('-p', '--print',help='Print in PDF file', default='cluster.pdf')
parser.add_argument('-d', '--detector',help='Print in PDF file', default='CE65_4')

args = parser.parse_args()

import ROOT
from plot_util import *

args.print = args.output.replace('.root','.pdf')

ALICEStyle()
ROOT.gStyle.SetLineWidth(1)
ROOT.gStyle.SetOptTitle(1)
ROOT.gStyle.SetOptStat(1)

class Painter:
  def __init__(self, canvas, printer, **kwargs):
    self.canvas = canvas
    self.printer = printer     # Output PDF in 1 file
    # Configuration
    self.subPadNX = kwargs['nx'] if kwargs.get('nx') else 1
    self.subPadNY = kwargs['ny'] if kwargs.get('ny') else 1
    # Status
    self.padIndex = 0
    self.pageName = "Start"
    self.hasCover = False
    self.hasBackCover = False
    # Dump
    self.root_obj = []         # Temp storage to avoid GC
  def __del__(self):
    if(self.hasCover and not self.hasBackCover):
      self.PrintBackCover('')
  def ResetCanvas(self):
    self.canvas.Clear()
    self.canvas.Divide(self.subPadNX, self.subPadNY)
  def SetLayout(self, nx, ny):
    self.subPadNX = nx
    self.subPadNY = ny
    ResetCanvas()
  def GetLayout(self):
    return (self.subPadNX, self.subPadNY)
  def PrintCover(self, title = '', isBack = False):
    self.canvas.Clear()
    pTxt = ROOT.TPaveText(0.25,0.4,0.75,0.6, "brNDC")
    if(title == ''):
      if(isBack):
        pTxt.AddText('Thanks for your attention!')
      else:
        pTxt.AddText(self.canvas.GetTitle())
    else:
      pTxt.AddText(title)
    self.canvas.cd()
    self.canvas.Draw()
    pTxt.Draw()
    if(isBack):
      self.canvas.Print(self.printer + ')', 'Title:End')
    else:
      self.canvas.Print(self.printer + '(', 'Title:Cover')
    pTxt.Delete()
    self.ResetCanvas()
  def PrintBackCover(self, title=''):
    self.PrintCover(title, isBack=True)
  def NextPage(self, title=""):
    self.padIndex = 0
    if(title == ""):
      title = self.pageName
    self.canvas.Print(self.printer, f"Title:{title}")
    self.ResetCanvas()
  def NextPad(self, title=""):
    if(self.padIndex == self.subPadNX * self.subPadNY):
      self.NextPage()
    self.padIndex = self.padIndex + 1
    self.canvas.cd(self.padIndex)
    ROOT.gPad.SetMargin(0.15, 0.02, 0.15, 0.1)
  # Drawing - Histograms
  def DrawHist(self, htmp, title="", option="", optStat=True, samePad=False, optLogY=False):
    ROOT.gStyle.SetOptStat(optStat)
    if(title == ""):
      title = htmp.GetTitle()
    if(not samePad):
      self.NextPad(title)
    print("[+] DEBUG - Pad " + str(self.padIndex) + ' : ' + htmp.GetName())
    ROOT.gPad.SetLogy(optLogY)
    if(option == "colz"):
      zmax = htmp.GetBinContent(htmp.GetMaximumBin())
      htmp.GetZaxis().SetRangeUser(0.0 * zmax, 1.1 * zmax)
    htmp.Draw(option)
class CorryPainter(Painter):
  def __init__(self, canvas, printer, **kwargs):
    super().__init__(canvas, printer, **kwargs)
  # End - class CorryPainter

c = ROOT.TCanvas('cQA','Corry Performance Figures',2560, 1440)
c.SetMargin(0.15, 0.1, 0.15, 0.1)
c.Draw()
paint = CorryPainter(c, args.print, nx=4, ny=3)
paint.PrintCover()

corryHist = ROOT.TFile(args.file)

eventModule = "EventLoaderEUDAQ2"
clusterALPIDEModule = "ClusteringSpatial"
clusterModule = "ClusteringAnalog"
corrModule = "Correlations"
analysisModule = "AnalysisDUT"
trackingModule = "Tracking4D"
alignDUTModule = "AlignmentDUTResidual"
detector = args.detector

def DrawClusteringAnalog(self, dirCluster):
  # Init
  self.pageName = f"ClusteringAnalog - {detector}"
  # Drawing
  hMap = dirCluster.Get("clusterPositionLocal")
  self.DrawHist(hMap, "Cluster neighbours charge","colz")

  hSize = dirCluster.Get("clusterSize")
  hSize.GetXaxis().SetRangeUser(0,30)
  self.DrawHist(hSize, "clusterSize", optLogY=True)

  hSize = dirCluster.Get("clusterCharge")
  hSize.Rebin(int(100. / hSize.GetBinWidth(1)))
  hSize.GetXaxis().SetRangeUser(-5000,20000)
  self.DrawHist(hSize, "clusterSize", optLogY=True)

  hSize = dirCluster.Get("clusterSeedCharge")
  hSize.Rebin(int(100. / hSize.GetBinWidth(1)))
  hSize.GetXaxis().SetRangeUser(0,12000)
  self.DrawHist(hSize, "clusterSize", optLogY=True)

  hSize = dirCluster.Get("clusterNeighboursCharge")
  hSize.Rebin(int(100. / hSize.GetBinWidth(1)))
  hSize.GetXaxis().SetRangeUser(-5000,5000)
  self.DrawHist(hSize, "clusterSize", optLogY=True)

  hSize = dirCluster.Get("clusterNeighboursChargeSum")
  hSize.Rebin(int(100. / hSize.GetBinWidth(1)))
  hSize.GetXaxis().SetRangeUser(-5000,10000)
  self.DrawHist(hSize, "Cluster neighbours charge", optLogY=True)

  hRatio = dirCluster.Get("clusterChargeRatio")
  hRatio.GetXaxis().SetRangeUser(0,10)
  hRatio.GetYaxis().SetRangeUser(0,1.1)
  hPx = hRatio.ProfileX()
  hPx.SetLineColor(ROOT.kRed)
  hPx.SetLineStyle(ROOT.kDashDotted) # dash-dot
  hPx.SetMarkerColor(ROOT.kRed)
  hPx.SetLineWidth(1)
  self.DrawHist(hRatio, "Cluster charge ratio", "colz", False)
  hPx.Draw("same")

  hSize = dirCluster.Get("clusterSeedSNR")
  hSize.Rebin(int(0.5 / hSize.GetBinWidth(1)))
  hSize.GetXaxis().SetRangeUser(0,100)
  self.DrawHist(hSize, "clusterSeedSNR")

  hSize = dirCluster.Get("clusterNeighboursSNR")
  hSize.GetXaxis().SetRangeUser(-10,10)
  self.DrawHist(hSize, "clusterNeighboursSNR")

  hMap = dirCluster.Get("clusterSeed_Neighbours")
  hMap.GetYaxis().SetRangeUser(-4000,10000)
  self.DrawHist(hMap, "clusterSeed_Neighbours", "colz", False)

  hMap = dirCluster.Get("clusterSeed_NeighboursSNR")
  self.DrawHist(hMap, "clusterSeed_NeighboursSNR", "colz", False)

  hMap = dirCluster.Get("clusterSeed_NeighboursSum")
  hMap.GetYaxis().SetRangeUser(-4000,10000)
  self.DrawHist(hMap, "clusterSeed_NeighboursSum", "colz", False)

  hMap = dirCluster.Get("clusterSeed_Cluster")
  hMap.GetYaxis().SetRangeUser(-4000,10000)
  self.DrawHist(hMap, "clusterSeed_Cluster", "colz", False)

  hMap = dirCluster.Get("clusterSeedSNR_Cluster")
  self.DrawHist(hMap, "clusterSeedSNR_Cluster", "colz", False)

  hMap = dirCluster.Get("clusterChargeShape")
  hMap.GetXaxis().SetRangeUser(-5,5)
  self.DrawHist(hMap, "clusterChargeShape", "colz", False)

  hMap = dirCluster.Get("clusterChargeShapeSNR")
  hMap.GetXaxis().SetRangeUser(-5,5)
  self.DrawHist(hMap, "clusterChargeShapeSNR", "colz", False)

  hMap = dirCluster.Get("clusterChargeShapeRatio")
  hMap.GetXaxis().SetRangeUser(-5,5)
  hMap.GetYaxis().SetRangeUser(-0.5,1.1)
  hPx = hMap.ProfileX() # TODO: Re-normalized with counts in seed
  hPx.SetLineColor(ROOT.kRed)
  hPx.SetLineStyle(ROOT.kDashDotted) # dash-dot
  hPx.SetMarkerColor(ROOT.kRed)
  hPx.SetLineWidth(1)
  self.DrawHist(hMap, "clusterChargeShapeRatio", "colz", False)
  hPx.Draw("same")
  # Output
  self.NextPage()
  return None
CorryPainter.DrawClusteringAnalog = DrawClusteringAnalog

dirTmp = corryHist.Get(clusterModule)
if(dirTmp != None):
  paint.DrawClusteringAnalog(dirTmp.Get(detector))

def DrawAnalysisDUT(self, dirAna):
  # Init
  self.pageName = f"AnalysisDUT - {detector}"
  # Drawing  
  hMap = dirAna.Get("clusterMapAssoc")
  self.DrawHist(hMap, "clusterSize", "colz")
  # residualsX
  hSigX = dirAna.Get("global_residuals").Get("residualsX")
  hSigX.Rebin(int(1. / hSigX.GetBinWidth(1)))
  self.NextPad()
  hSigX.Fit("gaus","","",-50,50)
  hSigX.GetXaxis().SetRangeUser(-50,50)
  self.DrawHist(hSigX, "clusterSize", samePad=True)
  # residualsY
  hSigX = dirAna.Get("global_residuals").Get("residualsY")
  hSigX.Rebin(int(1. / hSigX.GetBinWidth(1)))
  self.NextPad()
  hSigX.Fit("gaus","","",-50,50)
  hSigX.GetXaxis().SetRangeUser(-50,50)
  self.DrawHist(hSigX, "clusterSize", samePad=True)
  # Output
  self.NextPage()
  return None
CorryPainter.DrawAnalysisDUT = DrawAnalysisDUT

dirTmp = corryHist.Get(analysisModule)
if(dirTmp != None):
  paint.DrawAnalysisDUT(dirTmp.Get(detector))

def DrawAlignmentDUT(self, dirAlign):
  # Init
  self.pageName = f"AlignmentDUT - {detector}"
  # Iterations
  grIter = dirAlign.Get(f"alignment_correction_displacementX_{detector}")
  grIter.SetTitle("Alignment correction on displacement - X")
  self.DrawHist(grIter, "alignmentX")
  grIter = dirAlign.Get(f"alignment_correction_displacementY_{detector}")
  grIter.SetTitle("Alignment correction on displacement - Y")
  self.DrawHist(grIter, "alignmentY")
  # Residual X
  hSigX = dirAlign.Get("residualsX")
  hSigX.Rebin(int(1. / hSigX.GetBinWidth(1))) #um
  self.NextPad()
  hSigX.Fit("gaus","","",-20,20)
  hSigX.GetXaxis().SetRangeUser(-50,50)
  self.DrawHist(hSigX, "residualsX", samePad=True)
  # Residual Y
  hSigX = dirAlign.Get("residualsY")
  hSigX.Rebin(int(1. / hSigX.GetBinWidth(1))) #um
  self.NextPad()
  hSigX.Fit("gaus","","",-20,20)
  hSigX.GetXaxis().SetRangeUser(-50,50)
  self.DrawHist(hSigX, "residualsY", samePad=True)
  self.NextPage("AlignmentDUTResidual")
  return None
CorryPainter.DrawAlignmentDUT = DrawAlignmentDUT

dirTmp = corryHist.Get(alignDUTModule)
if(dirTmp != None):
  paint.DrawAlignmentDUT(dirTmp.Get(detector))

paint.PrintBackCover()
corryHist.Close()
