# PLC_chill_tank_PID
Modeling for tuning process described in PLC talk forum thread cf. https://www.plctalk.net/qanda/showthread.php?t=128251

* Backlash modeled as actual valve position never decreasing unless whole-percentage-rounded, post-processed PID CV output position is 0% (valve closed)

Model with tuned PID, per @Mispeld, with anti-backlash
====
* Kc = 50
* Ti = 60
* Td = 0
* Update time = 45s
* Anti-backlash post-processing sends 0% signal (closing valve) for 2s for any decrease in whole-percentage-rounded PID CV output position
* Anti-backlash movement not shown in lower [CV, %] plot

![](https://github.com/drbitboy/PLC_chill_tank_PID/raw/master/images/anti_backlash_pid_050_060_000.png)

Model with PID tuned as in actual results, with backlash
====
* Kc = 5 (too small)
* Ti = 8 (too small)
* Td = 1.5 (not needed)
* Update time = 45s

![](https://github.com/drbitboy/PLC_chill_tank_PID/raw/master/images/backlash_model_pid_20210228.png)

Actual data, with PID tuned for cycling, with CV-to-valve backlash
====
* Kc = 5 (too small)
* Ti = 8 (too small)
* Td = 1.5 (not needed)
* Update time = 45s

![](https://github.com/drbitboy/PLC_chill_tank_PID/raw/master/images/backlash_model_data_20210228.png)

Model
====

![](https://github.com/drbitboy/PLC_chill_tank_PID/raw/master/images/slow_pide_model.png)

![](https://github.com/drbitboy/PLC_chill_tank_PID/raw/master/images/modeling.png)
