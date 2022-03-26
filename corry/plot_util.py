#!/bin/env python3

# Utility lib for corryvreckan plot

# Based on pyROOT
import ROOT
  # Colors
from ROOT import kBlack, kRed, kBlue, kGreen, kViolet, kCyan, kOrange, kPink, kYellow, kMagenta, kGray, kWhite
from ROOT import kFullCircle, kFullSquare, kOpenCircle, kOpenSquare, kOpenDiamond, kOpenCross, kFullCross, kFullDiamond, kFullStar, kOpenStar, kOpenCircle, kOpenSquare, kOpenTriangleUp, kOpenTriangleDown, kOpenStar, kOpenDiamond, kOpenCross, kOpenThreeTriangles, kOpenFourTrianglesX, kOpenDoubleDiamond, kOpenFourTrianglesPlus, kOpenCrossX, kFullTriangleUp, kOpenTriangleUp, kFullCrossX, kOpenCrossX, kFullTriangleDown, kFullThreeTriangles, kOpenThreeTriangles, kFullFourTrianglesX, kFullDoubleDiamond, kFullFourTrianglesPlus
import sys, os, time, math, json, logging
from array import array

# From ALICE collaboration editor guidelines
def ALICEStyle(graypalette = False):
  print("[-] INFO - Setting ALICE figure style")
  ROOT.gStyle.Reset("Plain")
  ROOT.gStyle.SetOptTitle(0)
  ROOT.gStyle.SetOptStat(0)
  if(graypalette):
    ROOT.gStyle.SetPalette(8,0)
  else:
    ROOT.gStyle.SetPalette(1)
  ROOT.gStyle.SetCanvasColor(10)
  ROOT.gStyle.SetCanvasBorderMode(0)
  ROOT.gStyle.SetFrameLineWidth(1)
  ROOT.gStyle.SetFrameFillColor(kWhite)
  ROOT.gStyle.SetPadColor(10)
  ROOT.gStyle.SetPadTickX(1)
  ROOT.gStyle.SetPadTickY(1)
  ROOT.gStyle.SetPadTopMargin(0.02)
  ROOT.gStyle.SetPadBottomMargin(0.12)
  ROOT.gStyle.SetPadLeftMargin(0.14)
  ROOT.gStyle.SetPadRightMargin(0.02)
  ROOT.gStyle.SetHistLineWidth(1)
  ROOT.gStyle.SetHistLineColor(kRed)
  ROOT.gStyle.SetFuncWidth(2)
  ROOT.gStyle.SetFuncColor(kGreen+3)
  ROOT.gStyle.SetLineWidth(2)
  ROOT.gStyle.SetLabelSize(0.045,"xyz")
  ROOT.gStyle.SetLabelOffset(0.01,"y")
  ROOT.gStyle.SetLabelOffset(0.01,"x")
  ROOT.gStyle.SetLabelColor(kBlack,"xyz")
  ROOT.gStyle.SetTitleSize(0.05,"xyz")
  ROOT.gStyle.SetTitleOffset(1.2,"y")
  ROOT.gStyle.SetTitleOffset(1.1,"x")
  ROOT.gStyle.SetTitleFillColor(kWhite)
  ROOT.gStyle.SetTextSizePixels(26)
  ROOT.gStyle.SetTextFont(42)
  ROOT.gStyle.SetLegendBorderSize(0)
  ROOT.gStyle.SetLegendFillColor(kWhite)
  ROOT.gStyle.SetLegendFont(42)

def PrintCover(pad, file, title = '', isBack = False):
  pad.Clear()
  pTxt = ROOT.TPaveText(0.25,0.4,0.75,0.6, "brNDC")
  if(title == ''):
    if(isBack):
      pTxt.AddText('Thanks for your attention!')
    else:
      pTxt.AddText(pad.GetTitle())
  else:
    pTxt.AddText(title)
  pad.cd()
  pad.Draw()
  pTxt.Draw()
  if(isBack):
    pad.Print(file + ')', 'Title:End')
  else:
    pad.Print(file + '(', 'Title:Cover')
  pTxt.Delete()
