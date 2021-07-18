# ITS3

## Threshold

__config_thr.py__ - Inter/Extrapolate scan data for VCASN <-> Threshold/e-
* Method: Cubic spline from Scipy (try pyROOT?)
* Threshold/Float -> DAC/Integer, __floor__ value as ".0f"

Case: Generate VCASN for configuration file
```python
import config_thr

THR_FIXED = list(range(5,31)) + [35,40]
config_thr.InitScanData('uITS3g2_0VBB.csv')
config_thr.ThresholdForConfig(THR_FIXED)

# Draw scan data, fit and selected thr. value
plt = config_thr.DrawThreshold('DUT0')
plt = config_thr.DrawAll('THRScan - uITS3g2_0VBB')

# Output for conf. file
config_thr.PrintConfig([50, 60])
```

Case: Check configuration file (now only for uITS3g1)
  TODO: Input line number of DUT VCASN in conf. file
```shell
./config_thr.py --csv [scan_data] --config [conf_dir]
```


## Runlist
__run_list.py__ - Print run list in beam test
* Walk data dir. and list file newer (mtime) than start
* Skip current run (mtime < now - 60s)
* Conf. name in 3rd line of raw data
* Convert VCASN to threshold by __config_thr__, return average value of all DUTs
* Nevent is hard coded as 300k
* *TODO*: use param file for different setup

Arguments
| Name        | Short           | Description  |
|------------- |:-------------:| -----|
|--run|-r |Running directory (~/eudaq2/user/ITS3/misc/)|
|	--start| -s|Start run number|
|	--data|-d|Data path|
|	--csv||Threshold scan data|
|--nothr||Disable threshold interpolation, output 100e- as default|

Output format:
```text
Run Number                   |  THRe  | Config                          | End   | Nevents | Size/MB | Comments
run285172379_210716212923.raw|  51 e- | uITS3g1_conf_3V_ithr_70-0.conf  | 21:38 |   300k  |     439 |
```