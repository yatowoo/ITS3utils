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
parser.add_argument('--taf', help='Noise map from TAF', type=str, default=None)
parser.add_argument('--mask', help='Mask file types', type=str, default='RTS,hot,bad')
parser.add_argument('--frac', help='Fraction inside 3 sigma, used for RTS', type=float, default=0.95)
parser.add_argument('--debug','-v', help='Debug for fitting by pixels', default=False, action='store_true')

args = parser.parse_args()

NX, NY = 64, 32
SUBMATRIX_EDGE = [21, 42, 64]
SUBMATRIX_NOISE_CUT = [200, 200, 30]
SUBMATRIX_BINWIDTH = [10, 10, 5]
NOISE_THRESHOLD = 500

qaFile = ROOT.TFile.Open(args.input)
hqa = qaFile.Get(f"h2qa_{args.signal}")
c = ROOT.TCanvas('c1','Noise QA', 1440, 1200)
c.Divide(2,2)
c.cd(1)
hqa.Draw('colz')
c.cd(2)

fitfcn = ROOT.TF1('fp','gaus',-2000,2000)
fitfcn.SetLineColor(ROOT.kRed)
hRMS = ROOT.TH1F('hrms','RMS;ADCu;# pixels',100,0,500)
gRMS = ROOT.TGraph()
hSigma = ROOT.TH1F('hsigma','#sigma (gaus fitting);ADCu;# pixels',100,0,500)
hFWHM = ROOT.TH1F('hFWHM','FWHM/2;ADCu;# pixels',100,0,500)
gSigma = ROOT.TGraph()
hDiff = ROOT.TH1F('hdiff','Noise difference;ADCu;# pixels',1000,-500,500)
hFrac = ROOT.TH1F('hfrac','Fraction of counts in 3#sigma region;Fraction_{3#sigma};# pixels', 100, 0.01, 1.01)
hPedestalMap = ROOT.TH2D('hPedestalpl1','Map of pixel pedestal;Pxiel X;Pixel Y;#pixels',
  64,-0.5,63.5,32,-0.5,31.5)
hNoiseMap = ROOT.TH2D('hnoisepl1','Map of pixel noise amplitude;Pxiel X;Pixel Y;#pixels',
  64,-0.5,63.5,32,-0.5,31.5)
hNoiseMapType = ROOT.TH2D('h2noisetype','Map of pixel noise type;Pxiel X;Pixel Y;#pixels',
  64,-0.5,63.5,32,-0.5,31.5)

# root_plot
root_objs = []
def newObj(obj):
  global root_objs
  root_objs.append(obj)
  return root_objs[-1]
def add_text(pave : ROOT.TPaveText, s : str, color=None, size=0.04, align=11, font=42):
  text = pave.AddText(s)
  text.SetTextAlign(align)
  text.SetTextSize(size)
  text.SetTextFont(font)
  if(color):
    text.SetTextColor(color)
  return text

def submatrix_id(ix, iy):
  for iSub, edge in enumerate(SUBMATRIX_EDGE):
    if ix < edge: return iSub
  return iSub
def gaus_int(hist : ROOT.TH1, mean, sigma, nSigma = 3):
  binLower = hist.FindBin( mean - nSigma * sigma)
  binUpper = hist.FindBin( mean + nSigma * sigma)
  centralCount = hist.Integral(binLower, binUpper)
  return float( centralCount / hist.GetEntries() )
def noise_fit(qadb):
  global c
  c.cd(2)
  if qadb.get('niter') is None:
    qadb['niter'] = 1
  else:
    qadb['niter'] += 1
  qadb['rms'] = qadb['noise'].GetRMS()
  peak = qadb['noise'].GetMaximum()
  halfLeft = qadb['noise'].FindFirstBinAbove(peak/2.)
  halfRight = qadb['noise'].FindLastBinAbove(peak/2.)
  qadb['FWHM'] = qadb['noise'].GetBinCenter(halfRight) - qadb['noise'].GetBinCenter(halfLeft)
  fitRange = min(0.8 * qadb['FWHM'], 2*qadb['rms'])
  resultPtr = qadb['noise'].Fit(fitfcn,"SQ","",qadb['noise'].GetMean()-fitRange, qadb['noise'].GetMean()+fitRange)
  qadb['chi2'] = resultPtr.Chi2()
  qadb['ndf'] = resultPtr.Ndf()
  qadb['mean'] = fitfcn.GetParameter(1)
  qadb['sigma'] = fitfcn.GetParameter(2)
  qadb['frac'] = gaus_int(qadb['noise'], qadb['mean'], qadb['sigma'])
  # Quality control
  qadb['type'] = noise_type(qadb)
  if(qadb['niter'] == 1 and qadb['type'] != 'normal'):
    qadb['noise'].Rebin(2)
    return noise_fit(qadb)
  elif(qadb['type'] == 'bad' and qadb['niter'] < 3):
    qadb['noise'].Rebin(2)
    return noise_fit(qadb)
  # Draw info.
  pave = newObj(ROOT.TPaveText(0.15, 0.6, 0.45, 0.88,'NDC'))
  pave.SetFillColor(ROOT.kWhite)
  add_text(pave, qadb['type'], font=62)
  add_text(pave, f'#sigma_{{fit}} = {qadb["sigma"]:.1f}')
  add_text(pave, f'#chi^{{2}} / NDF = {qadb["chi2"]:.1f} / {qadb["ndf"]}')
  add_text(pave, f'fraction_{{3#sigma}} = {qadb["frac"]:.3f}')
  add_text(pave, f'RMS = {qadb["rms"]:.1f}')
  add_text(pave, f'FWHM/2 = {qadb["FWHM"]*0.5:.1f}')
  pave.Draw('same')
  return resultPtr
def noise_type(qadb):
  if(qadb['sigma'] > NOISE_THRESHOLD):
    return 'bad'
  cut = SUBMATRIX_NOISE_CUT[submatrix_id(qadb['pos'][0],qadb['pos'][1])]
  if qadb['rms'] < cut:
    return 'normal'
  elif qadb['sigma'] < cut:
    return 'RTS'
  else:
    return 'hot'

# Read TAF noise map
if(args.taf is not None):
    with ROOT.TFile.Open(args.taf) as tafFile:
      mapTAF = tafFile.Get('hnoisepl1').Clone('h2noiseTAF')
      hTAF = tafFile.Get('hNoiseDistripl1').Clone('hnoiseTAF')
      hDiffTAF = ROOT.TH1F('hdiffTAF','Noise difference',1000,-500,500)
    args.taf = True
else:
  args.taf = False

# QA for each pixel
pixel_qa = []
for ipx in range(1,2048+1):
  pixel_qa.append({})
  qadb = pixel_qa[-1]
  qadb['id'] = ipx
  qadb['pos'] = (int((ipx-1)/NY), (ipx-1)%NY)
  ix, iy= qadb['pos']
  qadb['noise'] = hqa.ProjectionY(f'_py_{ipx}',ipx,ipx)
  qadb['noise'].Rebin(SUBMATRIX_BINWIDTH[submatrix_id(ix, iy)])
  #qadb['noise'].Rebin(2) # width = 10 -> 20
  qadb['noise'].SetTitle(f'Noise distribution - Pixel ({ix}, {iy})')
  _ = qadb['noise'].Sumw2()
  qadb['noise'].Draw()
  resultPtr = noise_fit(qadb)
  # Fill histograms
  hPedestalMap.Fill(ix, iy, qadb['mean'])
  hNoiseMap.Fill(ix, iy, qadb['sigma'])
  if(qadb['type'] == 'RTS'):
    hNoiseMapType.Fill(ix, iy, 1)
  elif(qadb['type'] == 'hot'):
    hNoiseMapType.Fill(ix, iy, 10)
  gRMS.AddPoint(ipx-1, qadb['rms'])
  gSigma.AddPoint(ipx-1, qadb['sigma'])
  hRMS.Fill(qadb['rms'])
  hSigma.Fill(qadb['sigma'])
  hFWHM.Fill(qadb['FWHM'] * 0.5)
  hFrac.Fill(qadb['frac'])
  # Difference
  noiseComp = f'> ({ix}, {iy}) {qadb["type"]} pixel found - RMS={qadb["rms"]:.1f} | Sigma={qadb["sigma"]:.1f} | FWHM/2={qadb["FWHM"]*0.5:.1f} |'
  if(args.taf):
    qadb['taf'] = mapTAF.GetBinContent(ix+1, iy+1)
    hDiffTAF.Fill(qadb['sigma'] - qadb['taf'])
    noiseComp  = noiseComp + f' TAF={qadb["taf"]:.1f} |'
  hDiff.Fill(qadb['sigma'] - qadb['rms'])
  if(args.debug):
    if(qadb['type'] == 'normal' and qadb['frac'] < args.frac):
      qadb['type'] = 'RTS'
  if(args.debug and qadb['type'].lower() in args.mask.lower()):
    resultPtr.Print()
    print(noiseComp)
    ROOT.gPad.Update()
    cmd = input()
    
# Drawing and output
c.cd(3)
hRMS.SetLineColor(ROOT.kBlack)
hRMS.Draw()
hSigma.SetLineColor(ROOT.kRed)
hSigma.Draw('same')
hFWHM.SetLineColor(ROOT.kBlue)
hFWHM.Draw('same')
if(args.taf):
  hTAF.SetTitle('TAF')
  hTAF.SetLineColor(ROOT.kGreen + 3)
  hTAF.Draw("same")
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
hDiff.SetTitle('Noise difference (#sigma - RMS)')
if(args.taf):
  hDiffTAF.SetLineColor(ROOT.kRed)
  hDiffTAF.Draw('same')
  hDiff.SetTitle('Noise difference')
  lgd = ROOT.TLegend(0.6, 0.7, 0.8, 0.88)
  lgd.AddEntry(hDiff, '#sigma - RMS')
  lgd.AddEntry(hDiffTAF, '#sigma - TAF')
  lgd.Draw('same')

# Summary
typeSum = [qadb['type'] for qadb in pixel_qa]
print('>>> Summary of Noise QA <<\n'
  f'Total:\t{len(typeSum)}\n'
  f'Normal:\t{typeSum.count("normal")}\n'
  f'RTS:\t{typeSum.count("RTS")}\n'
  f'Hot:\t{typeSum.count("hot")}\n'
  f'Bad:\t{typeSum.count("bad")}\n'
)
# Mask files for RTS and hot pixels
with open(f'{args.output}_mask.txt','w') as maskFile:
  for qadb in pixel_qa:
    if(qadb['type'].lower() not in args.mask.lower()): continue
    ix, iy= qadb['pos']
    maskFile.write(f'p\t{ix}\t{iy}\n')
  print(f'[-] Mask file write to {maskFile.name} ({args.mask})')

cmd = input("Exit after checking plots: <type enter>")

outputFile = ROOT.TFile(f'{args.output}.root','RECREATE')
outputFile.cd()
c.Write()
hqa.Write()
hNoiseMap.Write()
hPedestalMap.Write()
hNoiseMapType.Write()
hFrac.Write()
outputFile.Close()
qaFile.Close()

c.SaveAs(f'{args.output}.pdf')

