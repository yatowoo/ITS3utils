#!/bin/env python3

import sys, os, json,argparse
import math

parser = argparse.ArgumentParser(description='Post-processing script for corryvreckan')
parser.add_argument('-f', '--file',help='Output histogram from corry', default="analog-debug.root")
parser.add_argument('-p', '--print',help='Print in PDF file', default=None)
parser.add_argument('-d', '--detector',help='Print in PDF file', default='CE65_4')
parser.add_argument('-n', '--nrefs',help='Number of reference ALPIDE planes', default=4, type=int)
parser.add_argument('--charge-max', dest='CHARGE_MAX', help='Max charge for histograms binning', default=5000, type=float)
parser.add_argument('--charge-binwidth',dest='CHARGE_BINWIDTH', help='Charge bin width for histograms binning', default=25, type=float)
parser.add_argument('--fit-range',dest='GAUS_FIT', help='Fitting range for gaussian distribution, ratio as FWHM', default=1.0, type=float)
parser.add_argument('--noisy-freq', dest='NOISY_FREQUENCY', help='Threshold of hit frequency to identify noisy pixels', default=0.001, type=float)

args = parser.parse_args()

import ROOT
from plot_util import *

if(args.print is None):
  args.print = args.file.replace('.root','.pdf')
elif not args.print.endswith('.pdf'):
  args.print = args.print + '.pdf'

ALICEStyle()
ROOT.gStyle.SetLineWidth(1)
ROOT.gStyle.SetOptTitle(1)
ROOT.gStyle.SetOptStat(0)

def simple_efficiency(nsel, nall):
  if(nall < 1.):
    return (0., 0.)
  eff = float(nsel) / float(nall)
  lowerErrorEff = eff - ROOT.TEfficiency.ClopperPearson(nall, nsel, 0.683, False)
  upperErrorEff = ROOT.TEfficiency.ClopperPearson(nall, nsel, 0.683, True) - eff
  error = (upperErrorEff + lowerErrorEff) / 2.
  return (eff, error, lowerErrorEff, upperErrorEff)

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
    self.root_objs = []         # Temp storage to avoid GC
  def __del__(self):
    if(self.hasCover and not self.hasBackCover):
      self.PrintBackCover('')
  def new_obj(self, obj):
    self.root_objs.append(obj)
    return self.root_objs[-1]
  def add_text(self, pave : ROOT.TPaveText, s : str, color=None, size=0.04, align=11, font=42):
    text = pave.AddText(s)
    text.SetTextAlign(align)
    text.SetTextSize(size)
    text.SetTextFont(font)
    if(color):
      text.SetTextColor(color)
    return text
  def draw_text(self, xlow=0.25, ylow=0.4, xup=0.75, yup=0.6, text = '', size=0.04, font=42):
    pave = self.new_obj(ROOT.TPaveText(xlow, ylow, xup, yup, "brNDC"))
    pave.SetBorderSize(0)
    pave.SetFillStyle(0) # hollow
    pave.SetFillColor(ROOT.kWhite)
    if(text != ''):
      self.add_text(pave, text, size=size, font=font)
    return pave
  def ResetCanvas(self):
    self.canvas.Clear()
    self.canvas.Divide(self.subPadNX, self.subPadNY)
  def SetLayout(self, nx, ny):
    self.subPadNX = nx
    self.subPadNY = ny
    self.ResetCanvas()
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
  def draw_hist_text(self, hist):
    """Plot bin contect as text for ROOT.TH2
    """
    xlower = ROOT.gPad.GetLeftMargin()
    xupper = 1 - ROOT.gPad.GetRightMargin()
    ylower = ROOT.gPad.GetBottomMargin()
    yupper = 1 - ROOT.gPad.GetTopMargin()
    wx = (xupper - xlower) / hist.GetNbinsX()
    wy = (yupper - ylower) / hist.GetNbinsY()
    for iy in range(hist.GetNbinsY()):
      for ix in range(hist.GetNbinsX()):
        val = hist.GetBinContent(ix + 1, iy +1)
        pave = self.draw_text(ix * wx + xlower, iy * wy + ylower, (ix+1) * wx + xlower, (iy+1)*wx + xlower)
        self.add_text(pave,f'{val:.3f}',size=0.06, font=62, align=22)
        pave.Draw('same')
  def normalise_profile_y(self, hist):
    for ix in range(1,hist.GetNbinsX()+1):
      hpfx = hist.ProjectionY(f'_py_{ix}', ix, ix)
      norm = hpfx.GetMaximum()
      if norm < 1: continue
      for iy in range(1,hist.GetNbinsY()+1):
        raw = hist.GetBinContent(ix, iy)
        hist.SetBinContent(ix, iy, 100 * raw / norm)
      hpfx.Delete()
    return None
  def optimise_hist_gaus(self, hist, scale=1):
    peak = hist.GetMaximum()
    mean = hist.GetMean()
    rms = hist.GetRMS()
    halfLeft = hist.FindFirstBinAbove(peak/2.)
    halfRight = hist.FindLastBinAbove(peak/2.)
    center = 0.5 * (hist.GetBinCenter(halfRight) + hist.GetBinCenter(halfLeft))
    fwhm = hist.GetBinCenter(halfRight) - hist.GetBinCenter(halfLeft)
    if fwhm < 2 * hist.GetBinWidth(1):
      print(f'[X] Warning  - FWHM too narrow {center = }, {fwhm = }, {rms = }, {peak = }')
      return None
    fitRange = min(5 * rms, args.GAUS_FIT * fwhm)
    resultPtr = hist.Fit('gaus','SQ','', center - fitRange, center + fitRange)
    try:
      params = resultPtr.GetParams()
    except ReferenceError:
      print(f'[X] Warning  - Fitting failed with {center = }, {fwhm = }, {rms = }, {peak = }')
      return None
    drawRange = min(15 * rms, 10 * params[2])
    hist.GetXaxis().SetRangeUser(center - drawRange, center + drawRange)
    # Draw info
    pave = self.new_obj(ROOT.TPaveText(0.18, 0.55, 0.45, 0.85,'NDC'))
    pave.SetFillColor(ROOT.kWhite)
    self.add_text(pave, f'mean (#mu) = {params[1] * scale:.1f}')
    self.add_text(pave, f'#sigma = {params[2] * scale:.1f}')
    self.add_text(pave, f'#chi^{{2}} / NDF = {resultPtr.Chi2():.1f} / {resultPtr.Ndf()}')
    self.add_text(pave, f'RMS = {rms * scale:.1f}')
    self.add_text(pave, f'FWHM = {fwhm * scale:.1f}')
    pave.Draw('same')
    return resultPtr
  def DrawHist(self, htmp, title="", option="", optStat=False, samePad=False, optGaus=False, scale=1, **kwargs):
    ROOT.gStyle.SetOptStat(optStat)
    if(title == ""):
      title = htmp.GetTitle()
    if(not samePad):
      self.NextPad(title)
    print("[+] DEBUG - Pad " + str(self.padIndex) + ' : ' + htmp.GetName())
    if kwargs.get('optNormY') == True:
      self.normalise_profile_y(htmp)
    if(option == "colz"):
      zmax = htmp.GetBinContent(htmp.GetMaximumBin())
      htmp.GetZaxis().SetRangeUser(0.0 * zmax, 1.1 * zmax)
    if(htmp.ClassName().startswith('TH')):
      htmp.SetTitleSize(0.08, "XY")
      htmp.SetTitleOffset(0.8, "XY")
    htmp.Draw(option)
    if(optGaus): self.optimise_hist_gaus(htmp, scale)
    ROOT.gPad.SetLogx(kwargs.get('optLogX') == True)
    ROOT.gPad.SetLogy(kwargs.get('optLogY') == True)
    ROOT.gPad.SetLogz(kwargs.get('optLogZ') == True)
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
associationModule = 'DUTAssociation'
alignDUTModule = "AlignmentDUTResidual"
detector = args.detector

def DrawEventLoaderEUDAQ2(self, dirEvent):
  htmp = dirEvent.Get('eudaqEventStart')
  self.N_EVENT = htmp.GetEntries()
  return None
CorryPainter.DrawEventLoaderEUDAQ2 = DrawEventLoaderEUDAQ2
paint.DrawEventLoaderEUDAQ2(corryHist.Get(eventModule).Get('ALPIDE_0'))

def DrawClusteringAnalog(self, dirCluster, nextPage=True, suffix=''):
  # Init
  self.pageName = f"ClusteringAnalog - {detector}"
  # Drawing
  hMap = dirCluster.Get("clusterPositionLocal")
  self.DrawHist(hMap, option="colz")
  self.draw_text(0.55, 0.92, 0.95, 0.98, f'Total N_{{cluster}} : {hMap.GetEntries():.0f}', font=62, size=0.05).Draw("same")
    # Noisy pixel
  hHitFreq = self.new_obj(ROOT.TH1F(f'hHitFreq{suffix}','Hitmap by cluster (frequency);Frequency;# pixels',10000,0.,1.0))
  pavePixel = self.draw_text(0.7, 0.6, 0.85, 0.80)
  nNoisy = 0
  print('>>> Mask creation by output of ClusteringAnalog')
  for iy in range(1,hMap.GetNbinsY()+1):
    for ix in range(1,hMap.GetNbinsX()+1):
      clusterCount = hMap.GetBinContent(ix, iy)
      clusterFreq = clusterCount / self.N_EVENT
      hHitFreq.Fill(clusterFreq)
      if(clusterFreq > args.NOISY_FREQUENCY):
        self.add_text(pavePixel, f'({ix-1}, {iy-1}) - {clusterFreq:.1e} [{clusterCount:.0f}]', size=0.025)
        nNoisy += 1
        print(f'p\t{ix-1}\t{iy-1} # {clusterFreq:.1e} [{clusterCount:.0f}]')
  self.DrawHist(hHitFreq, optLogY=True, optLogX=True)
  hHitFreq.SaveAs('noisy_mask.root') # DEBUG
  nNoHits = hHitFreq.GetBinContent(hHitFreq.FindBin(0.))
  paveStat = self.draw_text(0.2, 0.2, 0.42, 0.30)
  self.add_text(paveStat, f'Event loaded : {self.N_EVENT:.0f}')
  self.add_text(paveStat, f'No hits pixels : {nNoHits:.0f}')
  paveStat.Draw('same')
  self.draw_text(0.5, 0.80, 0.85, 0.85, f'Noisy pixels (freq. > {args.NOISY_FREQUENCY}) : {nNoisy}').Draw('same')
  if(nNoisy < 10): pavePixel.Draw('same')

  hSize = dirCluster.Get("clusterSize")
  hSize.GetXaxis().SetRangeUser(0,25)
  self.DrawHist(hSize, "clusterSize", optLogY=True, optStat=True)

  hSize = dirCluster.Get("clusterCharge")
  hSize.Rebin(int(args.CHARGE_BINWIDTH / hSize.GetBinWidth(1)))
  hSize.GetXaxis().SetRangeUser(-0.05 * args.CHARGE_MAX,args.CHARGE_MAX)
  self.DrawHist(hSize, "clusterSize", optLogY=True)

  hSize = dirCluster.Get("clusterSeedCharge")
  hSize.Rebin(int(args.CHARGE_BINWIDTH  / hSize.GetBinWidth(1)))
  hSize.GetXaxis().SetRangeUser(0,args.CHARGE_MAX)
  self.DrawHist(hSize, "clusterSize", optLogY=True)

  hSize = dirCluster.Get("clusterNeighboursCharge")
  hSize.Rebin(int(args.CHARGE_BINWIDTH  / hSize.GetBinWidth(1)))
  hSize.GetXaxis().SetRangeUser(-0.05 * args.CHARGE_MAX, args.CHARGE_MAX)
  self.DrawHist(hSize, "clusterSize", optLogY=True)

  hSize = dirCluster.Get("clusterNeighboursChargeSum")
  hSize.Rebin(int(args.CHARGE_BINWIDTH  / hSize.GetBinWidth(1)))
  hSize.GetXaxis().SetRangeUser(-0.05 * args.CHARGE_MAX,args.CHARGE_MAX)
  self.DrawHist(hSize, "Cluster neighbours charge", optLogY=True)

  hSize = dirCluster.Get("clusterSeedSNR")
  hSize.Rebin(int(1 / hSize.GetBinWidth(1)))
  hSize.GetXaxis().SetRangeUser(0,100)
  hSize.GetYaxis().SetRangeUser(0,hSize.GetMaximum() * 1.2)
  self.DrawHist(hSize, "clusterSeedSNR")

  hSize = dirCluster.Get("clusterNeighboursSNR")
  hSize.GetXaxis().SetRangeUser(-3,20)
  self.DrawHist(hSize, "clusterNeighboursSNR", optLogY=False)

  hMap = dirCluster.Get("clusterSeed_Neighbours")
  hMap.GetXaxis().SetRangeUser(-0.1 * args.CHARGE_MAX, args.CHARGE_MAX)
  hMap.GetYaxis().SetRangeUser(-0.1 * args.CHARGE_MAX,args.CHARGE_MAX)
  self.DrawHist(hMap, "clusterSeed_Neighbours", "colz", False)

  hMap = dirCluster.Get("clusterSeed_NeighboursSNR")
  hMap.GetYaxis().SetRangeUser(-1,10)
  self.DrawHist(hMap, "clusterSeed_NeighboursSNR", "colz", False)

  hMap = dirCluster.Get("clusterSeed_NeighboursSum")
  hMap.GetXaxis().SetRangeUser(-0.1 * args.CHARGE_MAX, args.CHARGE_MAX)
  hMap.GetYaxis().SetRangeUser(-0.1 * args.CHARGE_MAX, args.CHARGE_MAX)
  self.DrawHist(hMap, "clusterSeed_NeighboursSum", "colz", False)

  hMap = dirCluster.Get("clusterSeed_Cluster")
  hMap.GetXaxis().SetRangeUser(-0.1 * args.CHARGE_MAX, args.CHARGE_MAX)
  hMap.GetYaxis().SetRangeUser(-0.1 * args.CHARGE_MAX,args.CHARGE_MAX)
  self.DrawHist(hMap, "clusterSeed_Cluster", "colz", False)

  hMap = dirCluster.Get("clusterSeedSNR_Cluster")
  hMap.GetYaxis().SetRangeUser(-0.1 * args.CHARGE_MAX, args.CHARGE_MAX)
  self.DrawHist(hMap, "clusterSeedSNR_Cluster", "colz", False)

  hMap = dirCluster.Get("clusterChargeShape")
  hMap.GetXaxis().SetRangeUser(-5,5)
  hMap.GetYaxis().SetRangeUser(-0.1 * args.CHARGE_MAX, args.CHARGE_MAX)
  self.DrawHist(hMap, "clusterChargeShape", "colz", False)

  hMap = dirCluster.Get("clusterChargeShapeSNR")
  hMap.GetXaxis().SetRangeUser(-5,5)
  self.DrawHist(hMap, "clusterChargeShapeSNR", "colz", False)

  hMap = dirCluster.Get("clusterChargeShapeRatio")
  hMap.GetXaxis().SetRangeUser(-5,5)
  hMap.GetYaxis().SetRangeUser(-0.05,1.2)
  hPx = hMap.ProfileX() # TODO: Re-normalized with counts in seed
  hPx.SetLineColor(ROOT.kBlack)
  hPx.SetLineStyle(ROOT.kDashDotted) # dash-dot
  hPx.SetMarkerColor(ROOT.kBlack)
  hPx.SetLineWidth(3)
  self.DrawHist(hMap, "clusterChargeShapeRatio", "colz", optNormY=True)
  hPx.Draw("same")

  # Charge sharing (ratio distribution)
  windowSize = 3.0
  hRatioMean = self.new_obj(ROOT.TH2D(
    f'hChargeSharingRatioMean{suffix}',
    'CE65 - charge sharing by ratio (avg.);column (pixel);row (pixel)',
    int(windowSize), -windowSize/2, windowSize/2,
    int(windowSize), -windowSize/2, windowSize/2))
  hRatioMPV = self.new_obj(ROOT.TH2D(
    f'hChargeSharingRatioMPV{suffix}',
    'CE65 - charge sharing by ratio (MPV);column (pixel);row (pixel)',
    int(windowSize), -windowSize/2, windowSize/2,
    int(windowSize), -windowSize/2, windowSize/2))
  for iy in range(int(windowSize)):
    for ix in range(int(windowSize)):
      index = int(ix + iy * windowSize - (windowSize * windowSize  -1) // 2)
      binx = hMap.GetXaxis().FindBin(index)
      hpfy = hMap.ProjectionY(f'_py_{ix}_{iy}_{suffix}',binx,binx)
      hRatioMean.SetBinContent(ix + 1, iy + 1, hpfy.GetMean())
      peak = hpfy.GetBinCenter(hpfy.GetMaximumBin())
      hRatioMPV.SetBinContent(ix + 1, iy + 1, peak)
      hpfy.Delete()
  self.DrawHist(hRatioMean, 'hChargeSharingRatioMean', 'colz')
  self.draw_hist_text(hRatioMean)
  self.DrawHist(hRatioMPV, 'hChargeSharingRatioMPV', 'colz')
  self.draw_hist_text(hRatioMPV)
    # Cluster shape with highest N/Nth pixels
  hRatio = dirCluster.Get("clusterChargeRatio")
  hRatio.SetXTitle(f'R_{{n}} (#sum highest N pixels)')
  hRatio.SetYTitle('accumulated charge ratio')
  hRatio.GetXaxis().SetRangeUser(0,10)
  hRatio.GetYaxis().SetRangeUser(0,1.2)
  hPx = hRatio.ProfileX()
  hPx.SetLineColor(ROOT.kBlack)
  hPx.SetLineStyle(ROOT.kDashDotted) # dash-dot
  hPx.SetLineWidth(3)
  hPx.SetMarkerColor(ROOT.kBlack)
  self.DrawHist(hRatio, "Cluster charge ratio", "colz", False, optNormY=True)
  hPx.Draw("same")

  hRatio = dirCluster.Get('clusterChargeHighestNpixels')
  hRatio.SetTitle('accumulated charge - Highest N pixel ')
  hRatio.SetYTitle('accumulated charge')
  hRatio.SetXTitle(f'Q_{{n}} (#sum highest N pixels)')
  hRatio.GetXaxis().SetRangeUser(0,10)
  hRatio.GetYaxis().SetRangeUser(0,args.CHARGE_MAX)
  hPx = hRatio.ProfileX()
  hPx.SetLineColor(ROOT.kBlack)
  hPx.SetLineStyle(ROOT.kDashDotted) # dash-dot
  hPx.SetMarkerColor(ROOT.kBlack)
  hPx.SetLineWidth(3)
  self.DrawHist(hRatio, "Highest N pixel accumulated charge", "colz", False)
  hPx.Draw("same")
  # Output
  if(nextPage): self.NextPage()
  return None
CorryPainter.DrawClusteringAnalog = DrawClusteringAnalog

dirTmp = corryHist.Get(clusterModule)
if(dirTmp != None):
  paint.DrawClusteringAnalog(dirTmp.Get(detector))

def DrawCorrelation(self, dirCorr):
  # Init
  self.pageName = f"Correlations"
  detList = [detector] + [f'ALPIDE_{x}' for x in range(args.nrefs)]
  for detName in detList:
    dirDet = dirCorr.Get(detName)
    if(dirDet == None): continue
    self.DrawHist(dirDet.Get('hitmap_clusters'), option='colz')
    self.DrawHist(dirDet.Get('correlationX'), optGaus=True, scale=1000)
    self.DrawHist(dirDet.Get('correlationY'), optGaus=True, scale=1000)
  # Output
  self.NextPage()
  return None
CorryPainter.DrawCorrelation = DrawCorrelation

dirTmp = corryHist.Get(corrModule)
if(dirTmp != None):
  paint.DrawCorrelation(dirTmp)

def DrawTracking4D(self, dirAna):
  # Init
  self.pageName = f"Tracking4D - {args.nrefs} references"
  # Drawing
  h = dirAna.Get("tracksPerEvent")
  h.GetXaxis().SetRangeUser(-0.5,10)
  self.DrawHist(h, "tracksPerEvent", optLogY=True)
  h = dirAna.Get("trackChi2ndof")
  h.GetXaxis().SetRangeUser(0,20)
  self.DrawHist(h, "trackChi2ndof", optLogY=True)
  # Residuals in each plane
  for iRef in range(args.nrefs):
    refName = f'ALPIDE_{iRef}'
    dirRef = dirAna.Get(refName).Get('global_residuals')
    h = dirRef.Get('GlobalResidualsX')
    self.DrawHist(h, 'GlobalResidualsX', optGaus=True, scale=1000)
    h = dirRef.Get('GlobalResidualsY')
    self.DrawHist(h, 'GlobalResidualsY', optGaus=True, scale=1000)
  # Interception in DUT
  dirDUT = dirAna.Get(detector)
  if(dirDUT != None):
    self.DrawHist(dirDUT.Get('local_intersect'), option='colz')
  # Output
  self.NextPage()
  return None
CorryPainter.DrawTracking4D = DrawTracking4D

dirTmp = corryHist.Get(trackingModule)
if(dirTmp != None):
  paint.DrawTracking4D(dirTmp)

def DrawDUTAssociation(self, dirAna):
  # Init
  self.pageName = f"DUTAssociation - {detector}"
  # Drawing
  htmp = dirAna.Get('hTrackDUT')
  htmp.GetYaxis().SetRangeUser(-500, 500)
  htmp.GetXaxis().SetRangeUser(-500, 500)
  self.DrawHist(htmp, option='colz')
  htmp = dirAna.Get('hResidualX')
  self.DrawHist(htmp, optGaus=True)
  htmp = dirAna.Get('hResidualY')
  self.DrawHist(htmp, optGaus=True)
  # Output
  self.NextPage()
  return None
CorryPainter.DrawDUTAssociation = DrawDUTAssociation

dirTmp = corryHist.Get(associationModule)
if(dirTmp != None):
  paint.DrawDUTAssociation(dirTmp.Get(detector))

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
  self.DrawHist(hSigX, "residualsX", optGaus=True)
  # Residual Y
  hSigX = dirAlign.Get("residualsY")
  hSigX.Rebin(int(1. / hSigX.GetBinWidth(1))) #um
  self.DrawHist(hSigX, "residualsX", optGaus=True)
  self.NextPage("AlignmentDUTResidual")
  return None
CorryPainter.DrawAlignmentDUT = DrawAlignmentDUT

dirTmp = corryHist.Get(alignDUTModule)
if(dirTmp != None):
  paint.DrawAlignmentDUT(dirTmp.Get(detector))

def DrawAnalysisDUT(self, dirAna, nextPage=True):
  # Init
  self.pageName = f"AnalysisDUT - {detector}"
  # Summary pad
  hCut = dirAna.Get("hCutHisto")
  self.NextPad()
  nTrack = int(hCut.GetBinContent(1))
  nTrackCutChi2 = int(hCut.GetBinContent(2))
  nTrackCutDUT = int(hCut.GetBinContent(3))
  nTrackCutROI = int(hCut.GetBinContent(4))
  nTrackCutMask = int(hCut.GetBinContent(2))
  nTrackPass = int(hCut.GetBinContent(7))
  nAssociatedCluster = int(hCut.GetBinContent(8))
  eff, error, lerr, uerr = simple_efficiency(nAssociatedCluster, nTrackPass)
  pave = self.draw_text(0.15, 0.1, 0.7, 0.9)
  self.add_text(pave, f'Raw efficiency : {eff * 100:.1f}^{{+{uerr * 100:.1f}}}_{{-{lerr * 100:.1f}}} %', font=62, size=0.08)
  self.add_text(pave, f'All tracks N_{{trk}} : {nTrack:.0f}', font=62, size=0.05)
  self.add_text(pave, f'- #chi^{{2}} / Ndf > 3 : -{nTrackCutChi2}')
  self.add_text(pave, f'- outside DUT : -{nTrackCutDUT}')
  self.add_text(pave, f'- outside ROI : -{nTrackCutROI}')
  self.add_text(pave, f'- close to mask : -{nTrackCutMask}')
  self.add_text(pave, f'Track pass selectoin : {nTrackPass}', font=62, size=0.05)
  self.add_text(pave, f'Associated clusters N_{{assoc. cls.}} : {nAssociatedCluster}', font=62, size=0.05)
  pave.Draw()
  # Drawing  
  hMap = dirAna.Get("clusterMapAssoc")
  self.DrawHist(hMap, "clusterSize", "colz")
  # Charge
  hCharge = dirAna.Get('clusterChargeAssociated')
  hCharge.Rebin(int(args.CHARGE_BINWIDTH / hCharge.GetBinWidth(1)))
  hCharge.GetXaxis().SetRangeUser(0,args.CHARGE_MAX)
  self.DrawHist(hCharge)
  hCharge = dirAna.Get('seedChargeAssociated')
  hCharge.Rebin(int(args.CHARGE_BINWIDTH / hCharge.GetBinWidth(1)))
  hCharge.GetXaxis().SetRangeUser(0,args.CHARGE_MAX)
  self.DrawHist(hCharge)
  # residualsX
  hSigX = dirAna.Get("global_residuals").Get("residualsX")
  hSigX.Rebin(int(1. / hSigX.GetBinWidth(1)))
  self.DrawHist(hSigX, optGaus=True)
  # residualsY
  hSigX = dirAna.Get("global_residuals").Get("residualsY")
  hSigX.Rebin(int(1. / hSigX.GetBinWidth(1)))
  self.DrawHist(hSigX, optGaus=True)
  # Output
  if(nextPage): self.NextPage()
  return None
CorryPainter.DrawAnalysisDUT = DrawAnalysisDUT

dirTmp = corryHist.Get(analysisModule)
if(dirTmp != None):
  paint.DrawAnalysisDUT(dirTmp.Get(detector))

def DrawAnalysisCE65(self, dirAna, nextPage=True):
  # Init
  self.pageName = f"AnalysisCE65"
  # AnalysisDUT
  self.DrawAnalysisDUT(dirAna, nextPage=False)
  # Cluster analysis
  dirCluster = dirAna.Get('cluster')
  self.DrawClusteringAnalog(dirCluster, nextPage=False, suffix='_assoc')
  # Output
  self.pageName = f"AnalysisCE65"
  if(nextPage): self.NextPage()
  return None
CorryPainter.DrawAnalysisCE65 = DrawAnalysisCE65

dirTmp = corryHist.Get("AnalysisCE65")
if(dirTmp != None):
  paint.DrawAnalysisCE65(dirTmp.Get(detector))

paint.PrintBackCover()
corryHist.Close()
