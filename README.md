# PLC_chill_tank_PID
Modeling for tuning process described in PLC talk forum thread cf. https://www.plctalk.net/qanda/showthread.php?t=128251

### Model with tuned PID, per @Mispeld
* Kc = 50
* Ti = 60
* Td = 0
![](https://github.com/drbitboy/PLC_chill_tank_PID/raw/master/images/Kc50_T60_Td0.png)

### Model with PID tuned as in actual results
* Kc = 5 (too small)
* Ti = 8 (too small)
* Td = 1.5 (not needed)
![](https://github.com/drbitboy/PLC_chill_tank_PID/raw/master/images/Kc5_Ti8_Td1.5.png)

### Actual results with PID tuned for cycling
* Kc = 5 (too small)
* Ti = 8 (too small)
* Td = 1.5 (not needed)
![](https://github.com/drbitboy/PLC_chill_tank_PID/raw/master/images/model_20210217.png)

### Model
![](https://github.com/drbitboy/PLC_chill_tank_PID/raw/master/images/slow_pide_model.png)
