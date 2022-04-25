# ClusteringAnalog
**Maintainer**: Magnus Mager (<Magnus.Mager@cern.ch>), Yitao WU (<yitao.wu@cern.ch>)  
**Module Type**: *DETECTOR*  
**Detector Type**: *all*  
**Status**: Functioning

### Description
This module clusters the input data of a detector without individual hit timestamps.
It implements a series of requirements for analysing analogue sensors, including threshold cut, noise calibration, cluster window and plots for cluster characterisation.
The clustering method uses a threshold to select seed candidates in pixels and search neighbours in a square window with a given size around the seed pixel. With the maximum seeding method, only a single seed is kept and used for clustering. The cluster can also be defined and reconstructed by a charge-weighted center-of-gravity. See details below for other options.
For calibration, this module reads the pedestal and noise map for each pixel in the input file, which is prepared from external and specified in detector configuration.
Then in the clustering step, it will change to find seed and neighbours with threshold cut of signal/noise ratio instead of pixel charges.
To characterise the cluster shape, the charge distribution is estimated in the entire clustering window. The neighbouring pixels are ordered by 1D index number w.r.t. the local position of the seed. To understand the signal significance and consider the common shift effect, a special plot for charge ratio is accumulated with the largest N pixels in the cluster, using the sum of all positive pixels as the denominator to normalise cluster-by-cluster.
For digital sensors, when the pixel charge information is binary like ALPIDE, it takes the same strategy as module _ClusteringSpatial_. This feature can be enabled for a user-defined list of detector types.
These clusters are stored on the clipboard for each device.

### Parameters
* `reject_by_roi`: ROI rejection with the local position of the cluster. (Default: false)
* `window_size`: Matrix width around the seed to find neighbours. (Default: 3)
* `threshold_seed`: Cut on pixel charge to find seeds.
* `threshold_neighbour`: Cut on pixel charge to find neighbours.
* `thresholdSNR_seed`: S/N ratio cut for seeding, which is only used when detector `calibration_file` is available. If not defined, use the value of `threshold_seed`.
* `calibration_pedestal`: Histogram name of pedestal map in calibration file. Read as ROOT::TH2F.
* `calibration_noise`: Histogram name of noise map in calibration file. Read as ROOT::TH2F.
* `thresholdSNR_neighbour`: S/N ratio cut to find neighbours, which is only used when detector `calibration_file` is available. If not defined, use the value of `threshold_neighbour`.
* `method`: Clustering method to reconstruct cluster position and charge. Default option `cluster`, use charge-weighted center-of-gravity; Option `seed`, only use seed information; Option `sum3x3`, use all pixels in 3x3 matrix around the seed.
* `seeding_method`: Method to select seeds. Default option `multi`, select all pixels above the threshold for clustering and allow multiple clusters/hits in the same event; Option `max`, requires threshold cut as well but only keeps the single seed with maximum charge in pixels/seed candidates.
* `require_detectors`: simple event selection with ROI, used for quick check and alignment during beam test.

### Plots produced
For each detector, the following plots are produced:

* Histograms for the charge, S/N ratio, charge ratio of seed and neighbours.
* Cluster size and charge distribution.
* Correlation map for seed and neighbours, seed and cluster.
* 2D cluster positions in global and local coordinates

### Usage
```toml
[ClusteringAnalog]
reject_by_roi=true
window_size=3
threshold_seed=10                  # Used as thresholdSNR_seed, specify calibration_file in detector geometry
threshold_neighbour=-10            # Used as thresholdSNR_neighbour, specify calibration_file in detector geometry
method=cluster
seeding_method=multi
calibration_pedestal=hPedestalpl1  # CE65 calibration file from IPHC-TAF
calibration_noise=hnoisepl1        # CE65 calibration file from IPHC-TAF
```
