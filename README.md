# PLC_chill_tank_PID
Modeling for tuning process described in PLC talk forum thread cf. https://www.plctalk.net/qanda/showthread.php?t=128251

* CV-to-control valve position backlash modeled as actual valve position never decreasing unless whole-percentage-rounded, post-processed PID CV output position is 0% (valve closed; 4ma)

# Quickstart usage

    python pv_predict.py
    python pv_predict.py  --pid-Kc=50 --pid-Ti=60 --pid-Td=0 --fix-backlash --no-model-data

---
---

# Results

### Model four of four pieces:  process; PID tuned per @Mispeld; valve position backlash; backlash compensation to ensure control valve position matches PID CV output.
* The point of these plots is that @Mispeld's tuning parameters work well for this model if measures are taken to counteract valve position backlash when decreasing the PID CV signal
* Blue line in lower plot [CV, %] is PID CV output
* Orange line in lower plot is modeled valve position, excluding 2s intervals of backlash compensation at 0%
* Backlash compensation post-processes PID CV by sending 0% signal (closing valve) for 2s for any decrease in whole-percentage-rounded PID CV output position
* Backlash compensation events (i.e. valve position signal 0%=4ma when PID CV is 1% or more) are shown as green dots in lower plot
* Kc = 50
* Ti = 60
* Td = 0
* Update time = 45s

![](https://github.com/drbitboy/PLC_chill_tank_PID/raw/master/images/anti_backlash_pid_050_060_000.png)

---

### Model three of four pieces:  process; PID tuned as it was for actual data provided by @GrizzlyC; valve position backlash.  No backlash compensation.
* The point of these plots is that the process plus PID models represent the actual process with PID control reasonably well, assuming backlash is present
* Blue line in lower plot [CV, %] is PID CV output
* Orange line is model of valve position, __*with backlash*__, which does not follow any decrease in PID CV output until PID CV output is 0% (4ma)
* Kc = 5 (too small)
* Ti = 8 (too small)
* Td = 1.5 (not needed)
* Update time = 45s

![](https://github.com/drbitboy/PLC_chill_tank_PID/raw/master/images/backlash_model_pid_20210307.png)

---

### Model two of four pieces:  process and valve position backlash.  No backlash compensation.  Use actual PID CV output data for signal sent from PID to position valve.
* The point of these plots is that the process model represents the actual process reasonably well, assuming backlash is present
* Blue and orange lines are again PID CV output and backlash-modeled valve position, respectively
* Kc = 5 (too small)
* Ti = 8 (too small)
* Td = 1.5 (not needed)
* Update time = 45s

![](https://github.com/drbitboy/PLC_chill_tank_PID/raw/master/images/backlash_model_data_20210307.png)

---
---

# Process model

![](https://github.com/drbitboy/PLC_chill_tank_PID/raw/master/images/slow_pide_model.png)

![](https://github.com/drbitboy/PLC_chill_tank_PID/raw/master/images/modeling.png)

---
---

# Manifest

### ./

pv_predict.py - run process model against input PID CV value

pid.py - PID module, used by pv_predict.py

read_interleaved_XLSX.py - script to read data from Tank*.xlsx

Tank_20_Results_Feb_11-12_2021_R1.xlsx - one day of data from chill tank

.gitignore - list of files for Git to ignore

README.md - this file

---

### SmithPredictor/ - Smith Predictor code, modified from Peter Nachtwey's ZIP

SmithPredictor/SysID_SOPDT.py - main script to optimize 5-parameter model to data

SmithPredictor/Hotrod.txt - default Tab-Separated Values (TSV) original data for Smith Predictor

SmithPredictor/Tank_data_dbacklash.txt - TSV version of ../Tank*.xlsx data, with backlashed valve positions from PID CV data

SmithPredictor/readCSV.py - script to read TSV data

SmithPredictor/Chiller_result.png - Smith Predictor optimization result, using backlashed valve positions

SmithPredictor/original/SysID_SOPDT.zip - Peter's original ZIP, without hotrod.png

---

### images/ - Images used in top-level README.md

images/anti_backlash_pid_050_060_000.png - tuned PID modeling

images/backlash_model_pid_20210307.png - PID modeling using actual tuning paramaters

images/backlash_model_data_20210307.png - process modeling based on backlashed valve positions

images/slow_pide_model.* - sketch of fluid level as a proxy for chilled tank temperature

images/modeling.* - modeling equations

images/Kc50_Ti120_Td0.png - PID modeling with @GrizzlyC's later tuning; not used in README.md

---
---

# Python pre-requisites (Debian/Ubuntu naming)

* python-numpy
* python-pandas
* python-matplotlib
* python-scipy (for SmithPredictor)
