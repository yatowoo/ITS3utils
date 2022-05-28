#!/usr/bin/env python3

# Noise QA for analogue sensors

# Input: (N_EVENT, NX, NY, N_FRAME)

# Method for noise: RMS, sigma (gaus), FWHM, TAF

import argparse
import ROOT

parser = argparse.ArgumentParser(description='Analogue sensor noise QA')
parser.add_argument('input', help='Noise QA root file (TH2)')
parser.add_argument(
    '-o', '--output', help='Output file', default='noiseqa_debug')
parser.add_argument(
    '-s', '--signal', help='Signal method', default='cds')    
args = parser.parse_args()

qaFile = ROOT.TFile.Open(args.input)
hqa = qaFile.Get(f"h2qa_{args.signal}")
c = ROOT.TCanvas('c1','Noise QA', 1440, 1200)
c.Divide(2,2)
c.cd(1)
hqa.Draw('colz')
c.cd(2)

fitfcn = ROOT.TF1('fp','gaus',-2000,2000)
hRMS = ROOT.TH1F('hrms','RMS',100,0,500)
gRMS = ROOT.TGraph()
hSigma = ROOT.TH1F('hsigma','#sigma (gaus fitting)',100,0,500)
hFWHM = ROOT.TH1F('hFWHM','FWHM/2',100,0,500)
gSigma = ROOT.TGraph()
hDiff = ROOT.TH1F('hdiff','Noise difference',1000,-500,500)
pixel_qa = []
for ipx in range(1,2048+1):
  pixel_qa.append({})
  qadb = pixel_qa[-1]
  qadb['id'] = ipx
  qadb['noise'] = hqa.ProjectionY(f'_py_{ipx}',ipx,ipx)
  #qadb['noise'].Rebin(2) # width = 10 -> 20
  _ = qadb['noise'].Sumw2()
  qadb['noise'].Draw()
  qadb['rms'] = qadb['noise'].GetRMS()
  peak = qadb['noise'].GetMaximum()
  halfLeft = qadb['noise'].FindFirstBinAbove(peak/2.)
  halfRight = qadb['noise'].FindLastBinAbove(peak/2.)
  qadb['FWHM'] = qadb['noise'].GetBinCenter(halfRight) - qadb['noise'].GetBinCenter(halfLeft)
  fitRange = min(qadb['FWHM'] * 0.75, 2*qadb['rms'])
  resultPtr = qadb['noise'].Fit(fitfcn,"SQ","",-fitRange, fitRange)
  qadb['chi2'] = resultPtr.Chi2()
  qadb['ndf'] = resultPtr.Ndf()
  qadb['mean'] = fitfcn.GetParameter(1)
  qadb['sigma'] = fitfcn.GetParameter(2)
  gRMS.AddPoint(ipx-1, qadb['rms'])
  gSigma.AddPoint(ipx-1, qadb['sigma'])
  hRMS.Fill(qadb['rms'])
  hSigma.Fill(qadb['sigma'])
  hFWHM.Fill(qadb['FWHM'] * 0.5)
  hDiff.Fill(qadb['rms'] - qadb['sigma'])
  if(qadb['sigma'] > 200):
    resultPtr.Print()
    #cmd = input()

c.cd(3)
hRMS.SetLineColor(ROOT.kBlack)
hRMS.Draw()
hSigma.SetLineColor(ROOT.kRed)
hSigma.Draw('same')
hFWHM.SetLineColor(ROOT.kBlue)
hFWHM.Draw('same')
ROOT.gPad.BuildLegend(0.5,0.6,0.8,0.8)
ROOT.gStyle.SetOptStat(0)

c.cd(1)
gRMS.SetMarkerColor(ROOT.kBlack)
gRMS.SetLineColor(ROOT.kBlack)
gRMS.SetDrawOption("ALP")
gSigma.SetMarkerColor(ROOT.kRed)
gSigma.SetLineColor(ROOT.kRed)
gSigma.SetDrawOption("ALP")
gRMS.Draw("same")
gSigma.Draw("same")

c.cd(4)
hDiff.Draw()

cmd = input("Exit after checking plots: <type enter>")
c.SaveAs(f'{args.output}.pdf')

