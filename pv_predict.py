import os
import sys
import numpy as np
import traceback as tb
import read_interleaved_XLSX as riX

do_debug = 'DEBUG' in os.environ
do_warn = 'WARN' in os.environ

class CET:  ### Chilled Exothermic Tank
  """
Model temperature of PV sensor in tank with exothermic media and cooled
via jacket circulating chilled glycol 

Model

  Subscripts

    _T   - main Tank
    _ET  - Exotherm in main Tank
    _C2T - Chilled glycol heat xferred to main Tank (typically negative)
    _M2T - Measured tank volume (where PV is) heat xferred to main Tank

  Heat balance:  heat transferred into main Tank

    dQ_T     dQ_ET     dQ_C2T     dQ_M2T
    ----  =  -----  +  ------  +  ------
     dt       dt         dt         dt

  """
  ### Default model parameters
  default_Ke_per_h = 0.12     ### Exotherm-driven temperature rise, deg/h
  default_CVe = 3.07          ### CV where heat flow is balanced
  default_CVe0 = 0.95         ### CV valve is closed
  default_kPV = 0.9992        ### PV decay toward Tt(ank), per second
  default_time_step = 1.00    ### Time step, seconds
  default_init_temp = 11.87   ### Temperature to look for to start model
  default_init_CV = 0.0       ### CV to look for to start model
  default_pathv = ('Tank_20_Results_Feb_11-12_2021_R1.xlsx',)

  def __init__(self,*args,**keywords):
    """Initialize model parameters, read model data"""

    ### Model parameters
    self.Ke_per_h = float(keywords.get('Ke-per-h',self.default_Ke_per_h))
    self.CVe = float(keywords.get('CVe',self.default_CVe))
    self.CVe0 = float(keywords.get('CVe0',self.default_CVe0))
    self.init_temp = float(keywords.get('init-temp',self.default_init_temp))
    self.init_CV = float(keywords.get('init-CV',self.default_init_CV))
    self.kPV = float(keywords.get('kPV',self.default_kPV))
    self.time_step = float(keywords.get('time-step',self.default_time_step))
    self.do_plot = not keywords.get('no-plot',False)

    ### Model data from XLSX
    self.path = None
    for arg in args+self.default_pathv:
      try:
        assert self.path is None
        self.ats,self.cvs,self.pvs = riX.read_XLSX(arg)
        self.path = arg
        break
      except:
        if do_debug: tb.print_exc()
        if do_warn:
          sys.stderr.write('WARNING:  ignoring unknown argument [{0}]\n'.format(arg))

  def run_data(self,do_plot=None):

    ### Convert model parameters to per-timestep
    ### - Ke - exotherm-driven temperature rise per timestep
    ### - kPV_step - decay of PV toward Tt, per timestep
    Ke = self.Ke_per_h * self.time_step / 3600.0
    kPV_step = self.kPV**self.time_step

    ### Select start point from raw data
    i0 = np.where(np.bitwise_and(self.cvs==self.init_CV,self.pvs==self.init_temp))[0][0]-1

    ### Get model inputs
    pATs,pCVs = self.ats[i0:],self.cvs[i0:]

    ### Create predicted data arrays
    L = len(pATs)
    pPVs,pTts = np.zeros(L),np.zeros(L)
    pPV = self.init_temp
    pTt = pPV - (Ke / (1.0 - kPV_step))

    ### Initialize model
    AT,inext = pATs[0],0

    while True:
      if AT>=pATs[inext]:
        CV = pCVs[inext]
        pPVs[inext],pTts[inext] = pPV,pTt
        if CV > self.CVe0:
          CVscalar = (1.0 - ((CV - self.CVe0) / (self.CVe - self.CVe0))**0.85)
        else:
          CVscalar = 1.0
        inext += 1
        if inext==L: break

      pTt += CVscalar * Ke
      pPV = pTt + ((pPV - pTt) * kPV_step) + Ke

      ### Next time
      AT += self.time_step

    if self.do_plot if (None is do_plot) else do_plot:
      title = '{0}\nKe={1}deg/h kPV={2} CVe0={3} CVe={4} dt={5}'.format(
              os.path.basename(self.path)
              ,self.Ke_per_h
              ,self.kPV
              ,self.CVe0
              ,self.CVe
              ,self.time_step
              )
      self.plot_data(pATs,pPVs,pTts,title)

  def plot_data(self,ATs,PVs,Tts,title):
    import matplotlib.pyplot as plt

    fig,(pvplt,cvplt) = plt.subplots(nrows=2,ncols=1
                                    ,sharex=True
                                    ,gridspec_kw=dict(height_ratios=[3,1])
                                    )

    pvplt.axhline(12.0,label='SP',linewidth=0.5,linestyle='dotted')
    pvplt.plot(self.ats,self.pvs,label='PV Data')
    pvplt.plot(ATs,PVs,label='PV Predict')
    pvplt.plot(ATs,Tts,label='Tank Predict')
    pvplt.set_ylabel('Temperature, degC')
    pvplt.legend()
    pvplt.set_title(title)

    cvplt.plot(self.ats,self.cvs,label='CV Data',linewidth=0.5)
    cvplt.set_ylabel('PID CV out, %')
    cvplt.set_xlabel('Time, s')

    plt.show()

def process_args(argv):
  args,keywords = list(),dict()
  for arg in argv:
    if arg.startswith('--'):
      eqtoks = arg[2:].split('=')
      if 1==len(eqtoks): keywords[eqtoks[0]] = True
      else             : keywords[eqtoks[0]] = '='.join(eqtoks[1:])
    else:
      args.append(arg)

  return args,keywords

if "__main__" == __name__:
  args,keywords = process_args(sys.argv[1:])
  cet = CET(*args,**keywords).run_data()
