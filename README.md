# ITS3

## Threshold

__config_thr.py__ - Inter/Extrapolate scan data for VCASN <-> Threshold/e-
* Method: Cubic spline from Scipy (try pyROOT?)
* Threshold/Float -> DAC/Integer, __FLOOR__ value as ".0f"
* Data access: __config_thr.THR_DATA[chipID][ithr]__ (chipID=DUT0/1..)

|Keywords         | Description  |
|-------------| -----|
|vcasn, threshold|Scan data from CSV file|
|vcasn_fit, thr_fit|Fit data by Cubic-spline|
|vcasn_config, thr_config|Generated data for conf file|

Case: Generate VCASN for configuration file
```python
import config_thr

THR_FIXED = list(range(5,31)) + [35,40]
config_thr.InitScanData('uITS3g2_0V_scan.csv')
config_thr.ThresholdForConfig(THR_FIXED)

# Draw scan data, fit and selected thr. value
  # VCASN range: [40, 80] for 0V, [90, 140] for 3V
plt = config_thr.DrawAll('THRScan - uITS3g2_0VBB', [40,80])

# Output for conf. file
config_thr.PrintConfig(ithrList=[50, 60])
```

Case: Check configuration file (now only for uITS3g1)

* Compare the value with preset threshold. If some .conf file are completely SAME, try longer steps in high THR region.

TODO - Read .conf file to JSON/Dict
```shell

./config_thr.py --csv uITS3g2_0V_scan.csv --config $RUN_DIR/uITS3g2_conf_0V_ithr_50/
```

## Configuration file
__make_conf.py__ - Generate .conf files from Setup (JSON)

Usage: ./make_conf.py --setup,-s [Setup.json]
* Copy `Setup.json` and modify for new settings
* Notice `VCLIP` if change VBB, and alway create new data folder for new setup in `DataCollector.dc`

Output: `{title}_conf_{Vbb}V_ithr_{ithr}/{title}_conf_{Vbb}V_ithr_{ithr}-{thr}.conf`

Setup FILE (see example in `Setup.json`.)
|Keywords in *[general]*|Description|
|---|---|
|title|Name of setup, as prefix of .conf|
|eudaq|`$EUDAQ_DIR` with running script and `bin/euCliReader`|
|thr_scan|Threshold scan data^ for VCASN<->THR fitting|
|ithr_conf|ITHR list for .conf|
|thr_conf|Threshold list for .conf|
|setup|Chips order in .conf|
|Vbb|Setting for DUTs|
|ALPIDE|Basic settings for all chips^, specific in *[CHIPS]*|

^ Threshold scan data should be the same format as example file (like __uITS3g2_0V_scan.csv__).

## Runlist
__run_list.py__ - Print run list in beam test
* Walk data dir. and find all `*.raw` file
* Skip current run (mtime < now - 60s)
* Conf. name in first 10 lines of raw data
* Convert VCASN to threshold by __config_thr__, return average value of all DUTs
* Nevent from `$EUDAQ/bin/euCliReader` (but processing slowly)

Usage: ./run_list.py --setup [Setup.json] --data [$DATA_DIR] --run [$RUN_DIR] --eudaq [$EUDAQ_DIR]

Arguments
| Name        | Short           | Description  |
|------------- |:-------------:| -----|
|	--setup|-f|Setup file for configuration (see details above)|
|--run|-r |Running directory, also for configuration files ($EUDAQ/user/ITS3/misc/)|
|	--data|-d|Data directory (all raw file with the same setup, default: `DataCollector.dc/EUDAQ_FW_PATTERN`)|
|--eudaq||Path to find `bin/euCliReader`|
|--thr||Threshold scan data (.csv)|
|--nothr||Disable threshold interpolation, output 100e- as default|
|--log||Output short version for __eLog__ entry|
|--start|-s|Specify start run and append existed runlist|
|--debug|-v|Print debug info. (skip event number)|

CSV:
```text
RunNumber,Size,Config,Date,Time,VBB,Nevents,ITHR_DUT0,VCASN_DUT0,THRe_DUT0,...
```

Log:
```text
RunNumber                   |  THRe  | Config                          | End   | Nevents | Size   |
run285172379_210716212923.raw|  51 e- | uITS3g1_conf_3V_ithr_70-0.conf  | 21:38 |   300k  | 439.1MB|
```