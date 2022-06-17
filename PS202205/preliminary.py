#!/bin/env python3

# Plot preliminary results for approval

import plot_util
import ROOT
from copy import deepcopy
from pprint import pprint

# Binning: width, min, max
database = {
  'submatrix': ['AC','DC','SF'],
  'variant': ['A4', 'B4'],
  'A4':{
    'template': 'B4',
    'process': 'std',
    'noise':'qa/PS-A4_HV10-noisemap.root',
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
        'file':'output/',
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
        'file':'output/',
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
        'file':'output/',
      }
    },
  }
}
def dict_update(config : dict, template : dict):
  configNew = deepcopy(template)
  for k, v in config.items():
    if(v is dict):
      configNew[k] = dict_update(config[k], template[k])
    else:
      configNew[k] = deepcopy(v)
  return configNew
for chip in database['variant']:
  chipConfig = database[chip]
  if(chip == chipConfig.get('template')): continue
  database[chip] = dict_update(chipConfig, database[chipConfig['template']])

# Style
color_vars = {}
plot_util.COLOR_SET = plot_util.COLOR_SET_ALICE
for sub in database['submatrix']:
  color_vars[sub] = next(plot_util.COLOR)
marker_vars = {}
plot_util.MARKER_SET = plot_util.MARKER_SET_ALICE
for chips in database['variant']:
  marker_vars[chips] = next(plot_util.MARKER)

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
    hsub.GetYaxis().SetRangeUser(0, 1.3 * hsub.GetMaximum())
    painter.DrawHist(hsub, samePad=True)
  ROOT.gPad.SetLogy(False)
  # Legend
  lgd.Draw('same')
  # Text
  label = plot_util.InitALICELabel(type='ALICE ITS3-WP3 Preliminiary')
  label.Draw('same')
  ptxt = painter.draw_text(0.65, 0.75, 0.95, 0.92)
  painter.add_text(ptxt, f'Chip : CE65 (MLR1)')
  painter.add_text(ptxt, f'Process : {chip_vars["process"]} (split {chip_vars["split"]})')
  painter.add_text(ptxt,
    f'HV-AC = {chip_setup["HV"]}, V_{{psub}} = {chip_setup["PSUB"]}, V_{{pwell}} = {chip_setup["PWELL"]} (V)',
    size=0.03)
  ptxt.Draw('same')
  painter.NextPage()

def plot_cluster_charge(painter):
  """
  """

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
  painter.PrintBackCover('-')

if __name__ == '__main__':
  plot_preliminary()