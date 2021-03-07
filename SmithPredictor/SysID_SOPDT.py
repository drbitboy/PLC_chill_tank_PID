# -*- coding: utf-8 -*-
"""
Created on Thu Aug 10 13:59:32 2017

@author: Peter Nachtwey
Delta Computer Systems, Inc.

@modified:  Brian T. Carcich
Latchmoor Services, INC
"""
import sys
from math import sqrt
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from scipy.optimize import minimize
from scipy.integrate import odeint
from readCSV import readCSV

Hotrod_pv0 = [3.75733754,170.95853484,41.07003168,77.84619886,21.24783755]

def difeq(y, t, k, t0, t1, c, dt ):
    """ generate estimated SOPDT solution
        y[0] = process value
        y[1] = rate of change of the process value"""
    t = max(t-dt,0)
    _u = control_interp(t)              # offset CO for dead time
    _dy2dt = (-(t0+t1)*y[1]-y[0]+k*_u+c)/(t0*t1)    # SOPDT dif Eq
    return np.array([y[1], _dy2dt])


def t0p2(p, aTime, aPV):
    """find the values of a1 and a2 that minimize the ITAE3
p[0]:  open loop extend gain
p[1]:  time constant 0
p[2]:  time constant 1
p[3]:  output offset or bias
p[4]:  deadtime

"""
    _k,_t0,_t1,_c,_dt = p  #
    _pv0 = [aPV[0], 0.0]                # initial process value and rate
    _aEV = odeint(difeq, _pv0, aTime, args=(_k, _t0, _t1, _c, _dt))
    _sse = np.sum((aPV-_aEV[:,0])**2)
    print("sse = {}".format(_sse))
    return _sse


def plot_data(aTimes, aPV, aEV, aCO):
    """ plot the SOPDT response
        aTimes is the array of time values at which PV and CO data was taken
        aPV is the array of provided process variable
        aEV is the array of estimated process variable
        aCO is the array of provieded control output """
    _fig, (_ax0,_axCO,) = plt.subplots(nrows=2,ncols=1
                                      ,sharex=True
                                      ,gridspec_kw=dict(height_ratios=[3,1])
                                      )
    _fig.set_size_inches(6.0, 4.0)
    _line0, = _ax0.plot(aTimes, aPV,
                      'c-', label='process variable')
    _line1, = _ax0.plot(aTimes, aEV,
                      'r--', label='estimated value')
    _ax0.set_title('Process and Estimated Values vs Time')
    _ax0.set_ylabel('process and estimated values')

    _line2, = _axCO.plot(aTimes, aCO ,'g-',label='control %')
    _axCO.set_ylabel('control %')
    _axCO.set_xlabel('time')             # units are data dependent

    _lines = [_line0, _line1]
    _ax0.legend(_lines, [l.get_label() for l in _lines], loc='best')
    _fig.tight_layout()
    plt.show()


def go_main(method='Nelder-Mead',path='Hotrod.txt',pv0=Hotrod_pv0):
    """ enter path and file name for csv that has data to use for
 system identification.
 The file must have a header with three columns.
 Time, Control, and Process Variable
 Don't forget to change the delimiter for the ReadCSV function
 The time units are those used in the input file

 Arguments:

   method:  minimize method to read, Nelder-Mead or BFGS or Powell
   path:  CSV file for readCSV to read
   pv0:  initial guesses for the parameter array
           pv0[0]:  open loop extend gain
           pv0[1]:  time constant 0
           pv0[2]:  time constant 1
           pv0[3]:  output offset or bias
           pv0[4]:  deadtime

"""
    global control_interp
    # Parse pv0 argument if string
    if isinstance(pv0,str):
      lcl_pv0 = list(map(float,pv0.strip().lstrip('([').rstrip('])').split(',')))
    else:
      lcl_pv0 = pv0
    # tab separated variable with string header
    aTime, aCO, aPV = readCSV(path)
    N = len(aTime)
    aEV = np.zeros((N,2))               # estimated PV and PV'
    control_interp = interp1d(aTime, aCO, kind='linear',
                          bounds_error=False, fill_value='extrapolate')
    res = minimize(t0p2, lcl_pv0, args=(aTime, aPV), method=method)
    # do again to avoid local minimum
    res = minimize(t0p2, res.x, args=(aTime, aPV), method=method)
    print(res)
    k = res.x[0]        # open loop gain.  PV change / %control output
    t0 = res.x[1]       # time constant 0
    t1 = res.x[2]       # time constant 1
    c = res.x[3]        # PV offset, ambient PV
    dt = res.x[4]       # dead time
    # initial process value and rate of change
    pv1 = [aPV[0], (aPV[1]-aPV[0])/(aTime[1]-aTime[0])]
    aEV = odeint(difeq, pv1, aTime, args=(k, t0, t1, c, dt ))
    plot_data(aTime, aPV, aEV[:,0], aCO)
    print("RMS error          = {:7.3f}".format(sqrt(res.fun/len(aTime))))
    print("The open loop gain = {:7.3f} PV/%CO".format(res.x[0]))
    print("Time constant 0    = {:7.3f}".format(res.x[1]))
    print("Time constant 1    = {:7.3f}".format(res.x[2]))
    print("Ambient PV         = {:7.3f} in PV units".format(res.x[3]))
    print("Dead time          = {:7.3f}".format(res.x[4]))
    print("Time units are the same as provided in input file")
    # calculate the controller ISA PID parameters
    tc = max(0.1*max(t0,t1),0.8*dt)     # closed loop time constant
    kc = (t0+t1)/(k*(tc+dt))            # controller gain %CO/error
    ti = t0+t1                          # integrator time constant
    td = t0*t1/(t0+t1)                  # derivative time constant
    print("The closed loop time constant = {:7.3f}".format(tc))
    print("The controller gain           = {:7.3f} %CO/unit of error"
          .format(kc))
    print("The integrator time constant  = {:7.3f}".format(ti))
    print("The derivative time constant  = {:7.3f}".format(td))

if "__main__" == __name__:
    """
Usage:

  python                    \\
    SysID_SOPDT.py          \\
    [--path=Hotrod.txt]     \\
    [--method=Nelder-Mead]  \\
    [--pv0=3.757,170.959,41.070,77.846,21.248]

  OR

  python \\
    ../read_interleaved_XLSX.py \\
    ../Tank_20_Results_Feb_11-12_2021_R1.xlsx \\
    --decreasing-backlash \\
    --convert-to-tsv \\
    > Tank_data_dbacklash.txt

  python SysID_SOPDT.py --path=Tank_data_dbacklash.txt --pv0=-.074,6085.,2922.,12.25,0.033

"""
    kwargs = dict()
    for arg in sys.argv[1:]:
      if arg.startswith('--'):
        toks = arg[2:].split('=')
        key = toks.pop(0)
        L = len(toks)
        if L: val = '='.join(toks)
        else: val = True
        kwargs[key] = val

    go_main(**kwargs)
