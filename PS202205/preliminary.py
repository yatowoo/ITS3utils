#!/bin/env python3

# Plot preliminary results for approval

from turtle import color
import plot_util
import ROOT
from copy import deepcopy
from pprint import pprint

# Binning: width, min, max
database = {
  'submatrix': ['AC','DC','SF'],
  'variant': ['B4', 'A4'],
  'A4':{
    'template': 'B4',
    'process': 'std',
    'noise':'qa/PS-A4_HV10-noisemap.root',
    'AC':{
      'result':{
        'file': 'output/analysisCE65-AC_cls500snr3sum3x3_PS-A4_HV10.root',
      },
    },
    'DC':{
      'result':{
        'file': 'output/analysisCE65-DC_cls1200snr2sum3x3_PS-A4_HV10.root',
      },
    },
    'SF':{
      'result':{
        'file': 'output/analysisCE65-SF_cls300snr2sum3x3_PS-A4_HV10.root',
      },
    },
  },
  'B4_HV1':{
    'template': 'B4',
    'noise':'qa/PS-B4_HV1-noisemap.root',
    'setup':{
      'HV': 1,
      'PWELL': 0,
      'PSUB': 0,
    },
  },
  'B4':{
    'template': 'B4',
    'PIXEL_NX': 64,
    'PIXEL_NY': 32,
    'process': 'mod_gap',
    'split': 4,
    'setup':{
      'HV': 10,
      'PWELL': 0,
      'PSUB': 0,
    },
    'binning_noiseENC':[1.0, 0, 100],
    'binning_chargeENC':[50, 0, 5000],
    'noise':'qa/PS-B4_HV10-noisemap.root',
    'AC':{
      'title': 'AC amp.',
      'edge':[0, 20],
      'binning_noise':[5, 0, 400],
      'binning_charge':[100, 0, 15000],
      'calibration': 5.0,
      'result':{
        'seed_snr': 2,
        'seed_charge': 200,
        'cluster_charge': 1000,
        'file':'output/analysisCE65-AC_cls500snr3sum3x3_PS-B4_HV10.root',
      }
    },
    'DC':{
      'title': 'DC amp.',
      'edge':[21, 41],
      'calibration': 5.0,
      'binning_noise':[5, 0, 400],
      'binning_charge':[100, 0, 15000],
      'result':{
        'seed_snr': 2,
        'seed_charge': 200,
        'cluster_charge': 1000,
        'file':'output/analysisCE65-DC_cls500snr5sum3x3_PS-B4_HV10.root',
      }
    },
    'SF':{
      'title': 'SF',
      'edge':[42, 63],
      'calibration': 1.0,
      'binning_noise':[1, 0, 100],
      'binning_charge':[50, 0, 5000],
      'result':{
        'seed_snr': 2,
        'seed_charge': 200,
        'cluster_charge': 1000,
        'file':'output/analysisCE65-SF_cls250snr2sum3x3_PS-B4_HV10.root',
      }
    },
  }
}
def dict_update(config : dict, template : dict):
  configNew = deepcopy(template)
  for k, v in config.items():
    if(type(v) is dict):
      configNew[k] = dict_update(v, template[k])
    else:
      configNew[k] = deepcopy(v)
  return configNew
for chip in database['variant']:
  chipConfig = database[chip]
  if(chip == chipConfig.get('template')): continue
  database[chip] = dict_update(chipConfig, database[chipConfig['template']])

# Style
HIST_Y_SCALE = 1.4
color_vars = {}
plot_util.COLOR_SET = plot_util.COLOR_SET_ALICE
for sub in database['submatrix']:
  color_vars[sub] = next(plot_util.COLOR)
marker_vars = {}
line_vars = {}
plot_util.MARKER_SET = plot_util.MARKER_SET_ALICE
for chips in database['variant']:
  marker_vars[chips] = next(plot_util.MARKER)
  line_vars[chips] = next(plot_util.LINE)

def plot_alice(painter : plot_util.Painter, x1 = 0.02, y1 = 0.03, x2 = 0.35, y2 = 0.17, size=0.04):
  """
  """
  label = painter.new_obj(plot_util.InitALICELabel(x1, y1, x2, y2, 
    align=12, type='ALICE ITS3-WP3 Preliminiary'))
  painter.add_text(label, 'Beam test @CERN-PS May 2022, 10 GeV/#it{c} #pi^{-}', size=0.03)
  painter.add_text(label, f'Plotted on 17 Jun. 2022', size=0.03)
  label.Draw('same')
  return label

# Noise
def plot_noise(painter : plot_util.Painter, variant='B4'):
  """Noise distribution of each sub-matrix
  """
  painter.NextPad()
  painter.pageName = f'Noise - {variant}'
  chip_vars = database[variant]
  chip_setup = chip_vars['setup']
  noiseFile = ROOT.TFile.Open(chip_vars['noise'])
  hNoiseMap = noiseFile.Get('hnoisepl1')
  lgd = painter.new_obj(ROOT.TLegend(0.75, 0.55, 0.90, 0.7))
  histMax = 0
  for sub in database['submatrix']:
    vars = chip_vars[sub]
    hsub = painter.new_hist(f'hnoise_{chip}_{sub}','Noise Distribution;Equivalent Noise Charge (#it{e^{-}});# Pixels',
      chip_vars['binning_noiseENC'])
    hsub.SetLineColor(color_vars[sub])
    hsub.SetLineWidth(2)
    hsub.SetMarkerStyle(marker_vars[chip])
    hsub.SetMarkerColor(color_vars[sub])
    lgd.AddEntry(hsub,vars['title'])
    for ix in range(vars['edge'][0], vars['edge'][1]+1):
      for iy in range(chip_vars['PIXEL_NY']):
        hsub.Fill(hNoiseMap.GetBinContent(ix+1,iy+1) / vars['calibration'])
    if(hsub.GetMaximum() > histMax):
      histMax = hsub.GetMaximum()
    painter.DrawHist(hsub, samePad=True)
  painter.primaryHist.GetYaxis().SetRangeUser(0, HIST_Y_SCALE * histMax)
  ROOT.gPad.SetLogy(False)
  # Legend
  lgd.Draw('same')
  # Text
  plot_alice(painter)
  ptxt = painter.draw_text(0.65, 0.75, 0.95, 0.92)
  painter.add_text(ptxt, f'Chip : CE65 (MLR1)')
  painter.add_text(ptxt, f'Process : {chip_vars["process"]} (split {chip_vars["split"]})')
  painter.add_text(ptxt,
    f'HV-AC = {chip_setup["HV"]}, V_{{psub}} = {chip_setup["PSUB"]}, V_{{pwell}} = {chip_setup["PWELL"]} (V)',
    size=0.03)
  ptxt.Draw('same')
  painter.NextPage()

def plot_cluster_charge(painter : plot_util.Painter):
  """Cluster charge plot for all variants and sub-matrix
  """
  painter.pageName = 'Cluster Charge'
  histMax = 0
  lgd = painter.new_obj(ROOT.TLegend(0.60, 0.3, 0.90, 0.6))
  for chip in database['variant']:
    chip_vars = database[chip]
    for sub in database['submatrix']:
      sub_vars = chip_vars[sub]
      corry_vars = sub_vars['result']
      resultFile = ROOT.TFile.Open(corry_vars['file'])
      dirAna = resultFile.Get('AnalysisCE65')
      dirAna = dirAna.Get('CE65_4')
      hChargeRaw = painter.new_obj(dirAna.Get('clusterChargeAssociated').Clone(f'hClusterCharge_{chip}_{sub}'))
      hChargeRaw.SetDirectory(0x0)
      hCharge = painter.new_hist(f'hClusterChargeENC_{chip}_{sub}',
        'Cluster charge;Cluster charge (#it{e^{-}});# Entries;',
        chip_vars['binning_chargeENC'])
      hCharge.SetBit(ROOT.TH1.kIsNotW)
      hCharge.SetLineColor(color_vars[sub])
      hCharge.SetLineStyle(line_vars[chip])
      hCharge.SetMarkerColor(color_vars[sub])
      hCharge.SetMarkerStyle(marker_vars[chip])
      hCharge.SetMarkerSize(1.5)
      hCharge.SetDirectory(0x0)
      # Scale with calibration
      scale = sub_vars['calibration']
      binmin = hChargeRaw.FindBin(chip_vars['binning_chargeENC'][1] * scale)
      binmax = hChargeRaw.FindBin(chip_vars['binning_chargeENC'][2] * scale)
      for ix in range(binmin, binmax):
        calibratedX = hChargeRaw.GetBinCenter(ix) / scale
        val = hChargeRaw.GetBinContent(ix)
        hCharge.Fill(calibratedX, val)
      hCharge.Sumw2()
      if(hCharge.GetMaximum() > histMax):
        histMax = hCharge.GetMaximum()
      painter.hist_rebin(hChargeRaw, sub_vars['binning_charge'])
      # Draw
      painter.DrawHist(hCharge, samePad=True)
        # Fitting
      painter.optimise_hist_langau(hCharge, fitRange=[300, 1200],
        color=color_vars[sub], style=line_vars[chip], notext=True)
        # Legend
      lgd.AddEntry(hCharge, f'{chip_vars["process"]} {sub_vars["title"]}'
        f' (SNR_{{seed}}={corry_vars["seed_snr"]})')
      resultFile.Close()
  painter.primaryHist.GetYaxis().SetRangeUser(0, HIST_Y_SCALE * histMax)
  # Text
  lgd.SetTextSize(0.035)
  lgd.Draw('same')
  plot_alice(painter)
  ptxt = painter.draw_text(0.62, 0.75, 0.95, 0.92)
  painter.add_text(ptxt, f'Chip : CE65 (MLR1)')
  painter.add_text(ptxt, f'Process : std/mod_gap (split {chip_vars["split"]})')
  chip_setup = chip_vars['setup']
  painter.add_text(ptxt,
    f'HV-AC = {chip_setup["HV"]}, V_{{psub}} = {chip_setup["PSUB"]}, V_{{pwell}} = {chip_setup["PWELL"]} (V)',
    size=0.03)
  ptxt.Draw('same')
  painter.NextPage()

def plot_cluster_shape(painter):
  """
  """

def plot_tracking_residual(painter):
  """
  """

def plot_preliminary():
  plot_util.ALICEStyle()
  painter = plot_util.Painter(
    printer='preliminary.pdf',
    winX=1600, winY=1000, nx=1, ny=1)
  painter.PrintCover('CE65 Preliminary')
  plot_noise(painter,'B4')
  plot_noise(painter,'A4')
  plot_cluster_charge(painter)
  painter.PrintBackCover('-')

if __name__ == '__main__':
  plot_preliminary()
  #pprint(database)