# PLC_chill_tank_PID
Modeling for tuning process described in PLC talk forum thread cf. https://www.plctalk.net/qanda/showthread.php?t=128251

* CV-to-control valve position backlash modeled as actual valve position never decreasing unless whole-percentage-rounded, post-processed PID CV output position is 0% (valve closed; 4ma)

Model with tuned PID, per @Mispeld, and backlash model with anti-backlash action for modeled valve position
====
* Kc = 50
* Ti = 60
* Td = 0
* Update time = 45s
* Anti-backlash post-processes PID CV by sending 0% signal (closing valve) for 2s for any decrease in whole-percentage-rounded PID CV output position
* Anti-backlash events (i.e. valve position signal 0%=4ma when PID CV is 1% or more) are shown as green dots in lower plot [CV, %]
* The point of these plots is that the @Mispeld's tuning parameters work well for this model if measures are taken to counteract valve position backlash when decreasing the PID CV signal

![](https://github.com/drbitboy/PLC_chill_tank_PID/raw/master/images/anti_backlash_pid_050_060_000.png)

Model with modeled PID tuned as in actual results, with backlash model
====
* Kc = 5 (too small)
* Ti = 8 (too small)
* Td = 1.5 (not needed)
* Update time = 45s
* The point of these plots is that the process plus PID models represent the actual process with PID control reasonably well, assuming backlash is present

![](https://github.com/drbitboy/PLC_chill_tank_PID/raw/master/images/backlash_model_pid_20210307.png)

Actual data, including actual PID CV output data, with backlash model for modeled valve position, but PID control is not modeled
====
* Kc = 5 (too small)
* Ti = 8 (too small)
* Td = 1.5 (not needed)
* Update time = 45s
* The point of these plots is that the process model represents the actual process reasonably well, assuming backlash is present

![](https://github.com/drbitboy/PLC_chill_tank_PID/raw/master/images/backlash_model_data_20210307.png)

Model
====

![](https://github.com/drbitboy/PLC_chill_tank_PID/raw/master/images/slow_pide_model.png)

![](https://github.com/drbitboy/PLC_chill_tank_PID/raw/master/images/modeling.png)
