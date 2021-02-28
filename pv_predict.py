import os
import sys
import pid
import math
import numpy as np
import traceback as tb
import read_interleaved_XLSX as riX

do_debug = 'DEBUG' in os.environ
do_warn = 'WARN' in os.environ
npzs = lambda L: np.zeros(L,dtype=np.float)

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
  default_CVe = 3.6           ### CV where heat flow is balanced (-Ke)
  default_CVe0 = 0.9          ### CV valve is closed
  default_CVe_Ke_frac = 1.    ### fraction of Ke at CV=CVe
  default_CVexponent = 0.85   ### CV exponent for non-linear cooling(CV)
  default_kPV = 0.997         ### PV decay toward Tt(ank), per second
  default_time_step = 1.00    ### Time step, seconds
  default_init_temp = 11.87   ### Temperature to look for to start model
  default_init_CV = 0.0       ### CV to look for to start model

  ### Source data to which to compare model
  default_pathv = ('Tank_20_Results_Feb_11-12_2021_R1.xlsx',)

  ### Default PID parameters (poor control)
  default_pid_Kc = 5.0           ### Gain ratio
  default_pid_Ti = 8.0           ### minutes
  default_pid_Td = 1.5           ### minutes
  default_pid_updatetime = 45.0  ### seconds
  default_pid_deadband = 0.01    ### % of PV range
  default_pid_setpoint = 12.00   ### degrees Celsius
  default_pid_duration = 86400.  ### seconds

  def __init__(self,*args,**keywords):
    """Initialize model parameters, read model data"""

    ### Model parameter inputs
    self.Ke_per_h = float(keywords.get('Ke-per-h',self.default_Ke_per_h))
    self.CVe = float(keywords.get('CVe',self.default_CVe))
    self.CVe0 = float(keywords.get('CVe0',self.default_CVe0))
    self.CVe_Ke_frac = float(keywords.get('CVe0-Ke-frac',self.default_CVe_Ke_frac))
    self.CVexponent = float(keywords.get('CVexponent',self.default_CVexponent))
    self.init_temp = float(keywords.get('init-temp',self.default_init_temp))
    self.init_CV = float(keywords.get('init-CV',self.default_init_CV))
    self.kPV = float(keywords.get('kPV',self.default_kPV))
    self.model_time_step = float(keywords.get('model-time-step',self.default_time_step))
    self.do_plot = not keywords.get('no-plot',False)

    self.pid_Kc = float(keywords.get('pid-Kc',self.default_pid_Kc))
    self.pid_Ti = float(keywords.get('pid-Ti',self.default_pid_Ti))
    self.pid_Td = float(keywords.get('pid-Td',self.default_pid_Td))
    self.pid_updatetime = float(keywords.get('pid-updatetime',self.default_pid_updatetime))
    self.pid_deadband = float(keywords.get('pid-deadband',self.default_pid_Kc))
    self.pid_setpoint = float(keywords.get('pid-setpoint',self.default_pid_setpoint))
    self.pid_duration = float(keywords.get('pid-duration',self.default_pid_duration))

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

    self.calculate_per_timestep_parameters()

  def calculate_per_timestep_parameters(self):
    ### Convert model parameter inputs to per-timestep values
    ### - .Ke - temperature rise per timestep, exotherm-only, no cooling
    ### - .kPV_step - per-timestep PV decay, (PVn-Tt)/(PV<n-1>-Tt)
    self.Ke = self.Ke_per_h * self.model_time_step / 3600.0
    self.kPV_step = self.kPV**self.model_time_step

  def model_one_timestep(self,AT,Tt,PV,CVscalar):
    retTt = Tt + CVscalar
    retPV = retTt + ((PV - retTt) * self.kPV_step) + self.Ke
    retAT = AT + self.model_time_step
    return retAT,retTt,retPV

  def calculate_CVscalar(self,CV):
    if CV > self.CVe0: return self.Ke * (1.0 - (self.CVe_Ke_frac * ((CV - self.CVe0) / (self.CVe - self.CVe0))**self.CVexponent))
    return self.Ke

  def xCV_to_CV(self,xCV,lastblCV):
    rounded0_CV = round(xCV,0)
    if rounded0_CV > lastblCV: blCV = rounded0_CV
    elif rounded0_CV <= 0.0  : blCV = 0.0
    else                     : blCV = lastblCV
    return blCV,rounded0_CV,xCV,self.calculate_CVscalar(blCV)

  def model_data(self,do_plot=None):

    ### Select start point from raw data
    i0 = np.where(np.bitwise_and(self.cvs==self.init_CV,self.pvs==self.init_temp))[0][0]-1

    ### Get model inputs
    pATs,pCVs = self.ats[i0:],self.cvs[i0:]

    ### Create predicted data arrays
    L = len(pATs)
    pPVs,pTts,pblCVs = npzs(L),npzs(L),npzs(L)

    ### Get Present Value from model
    pPV = self.pvs[i0:i0+2].mean()
    ### Assuming pPV is steady at one value
    pTt = pPV - (self.Ke / (1.0 - self.kPV_step))

    ### Initialize model
    AT,inext,blCV = pATs[0],0,-1e32

    while True:
      if AT>=pATs[inext]:
        blCV,rCV,xCV,CVscalar = self.xCV_to_CV(pCVs[inext],blCV)
        pPVs[inext],pTts[inext],pblCVs[inext] = pPV,pTt,blCV
        inext += 1
        if inext>=L: break

      AT,pTt,pPV = self.model_one_timestep(AT,pTt,pPV,CVscalar)

    if self.do_plot if (None is do_plot) else do_plot:
      pvtitle = '{0}\nKe={1}deg/h kPV={2} CVe0/CVe/CVexp/KeFrac@CVe={3}/{4}/{5}/{6}'.format(
                os.path.basename(self.path)
                ,self.Ke_per_h
                ,self.kPV
                ,self.CVe0
                ,self.CVe
                ,self.CVexponent
                ,self.CVe_Ke_frac
                )
      #self.plot_data(pATs,None,pPVs,pTts,title,cvtitle=None)
      self.plot_data((self.ats,'CV',None,((self.cvs,'CV data',)
                                         ,)
                     ,)
                    ,(pATs,'CV',None,((pblCVs,'Backlash CV',)
                                     ,)
                     ,)
                    ,(self.ats,'PV',None,((self.pvs,'PV Data',)
                                         ,)
                     ,)
                    ,(pATs,'PV',pvtitle,((pTts,'Tank Predict',)
                                        ,(pPVs,'PV Predict',)
                                        ,)
                     ,)
                    )
    #if None is CVs:
    #  pvplt.plot(self.ats,self.pvs,label='PV Data')
    #pvplt.plot(ATs,PVs,label='PV Predict')
    #pvplt.plot(ATs,Tts,label='Tank Predict')

    #if None is CVs:
    #  cvplt.plot(self.ats,self.cvs,linewidth=0.5)
    #else:
    #  cvplt.plot(ATs,CVs,linewidth=0.5)

  def plot_datax(self,ATs,CVs,PVs,Tts,title,cvtitle=None):pass
  def plot_data(self,*args):
    import matplotlib.pyplot as plt

    fig,(pvplt,cvplt) = plt.subplots(nrows=2,ncols=1
                                    ,sharex=True
                                    ,gridspec_kw=dict(height_ratios=[3,1])
                                    )

    pvplt.axhline(12.0,label='SP',linewidth=0.5,linestyle='dotted')
    pvplt.set_ylabel('Temperature, degC')
    #pvplt.set_title(title)
    cvplt.set_ylabel('CV, %')
    cvplt.set_xlabel('Time, s')

    for ats,whichplot,xvtitle,xvpairs in args:
      xvplt = 'CV' == whichplot and cvplt or pvplt
      if isinstance(xvtitle,str): xvplt.set_title(xvtitle)
      for xvs,xvlegend in xvpairs:
        sys.stdout.flush()
        xvplt.plot(ats,xvs,label=xvlegend)
      xvplt.legend(loc='best')

    #if None is CVs:
    #  pvplt.plot(self.ats,self.pvs,label='PV Data')
    #pvplt.plot(ATs,PVs,label='PV Predict')
    #pvplt.plot(ATs,Tts,label='Tank Predict')

    #if None is CVs:
    #  cvplt.plot(self.ats,self.cvs,linewidth=0.5)
    #else:
    #  cvplt.plot(ATs,CVs,linewidth=0.5)

    #if isinstance(cvtitle,str): cvplt.set_title(cvtitle)

    plt.show()

  def model_with_pid(self,keywords,do_plot=None):
    L = int(math.ceil(self.pid_duration / self.pid_updatetime))
    (ATs,rPVs,xTts,rCVs,blCVs,xCVs
    ,) = npzs(L),npzs(L),npzs(L),npzs(L),npzs(L),npzs(L)
    AT,xPV,xTt,xCV = 0.0,11.80,11.80,0.0

    nextPIDAT,inext,blCV = 0.0,0,-1e32

    ctlpid = pid.PID(self.pid_Kc,self.pid_Ti,self.pid_Td
                    ,CVlast=xCV
                    ,Updatetime=self.pid_updatetime
                    ,Deadband=self.pid_deadband
                    )

    while True:
      rPV = round(xPV,2)

      if AT >= nextPIDAT:
        xCV = ctlpid.control(rPV,self.pid_setpoint)
        blCV,rCV,xCV,CVscalar = self.xCV_to_CV(xCV,blCV)
        """
        xCV = ctlpid.control(rPV,self.pid_setpoint)
        rCV = round(xCV,0)
        if rCV > blCV  : blCV = rCV
        elif rCV <= 0.0: blCV = 0.0
        if blCV != lxastblCV:
          CVscalar = self.calculate_CVscalar(blCV)
          lxastblCV = blCV
        """
        (ATs[inext],rPVs[inext],xTts[inext]
        ,rCVs[inext],xCVs[inext],blCVs[inext]
        ,) = AT,rPV,xTt,rCV,xCV,blCV
        inext += 1
        if inext >= L: break
        nextPIDAT = AT + self.pid_updatetime

      AT,xTt,xPV = self.model_one_timestep(AT,xTt,xPV,CVscalar)

    if self.do_plot if (None is do_plot) else do_plot:
      pvtitle = 'Ke={0}deg/h kPV={1} CVe0={2} CVe={3} CVexp={4}'.format(
                self.Ke_per_h
                ,self.kPV
                ,self.CVe0
                ,self.CVe
                ,self.CVexponent
                )
      cvtitle = 'Kc={0} Ti={1}min Td={2}min Update={3}s'.format(
                self.pid_Kc
                ,self.pid_Ti
                ,self.pid_Td
                ,self.pid_updatetime
                #,self.pid_deadband
                )
      self.plot_data((ATs,'CV',cvtitle,((rCVs,'Rounded CV',)
                                       ,(blCVs,'Backlash CV',)
                                       ,)
                     ,)
                    ,(ATs,'PV',pvtitle,((xTts,'Tank Predict',)
                                       ,(rPVs,'PV Predict',)
                                       ,)
                     ,)
                    )


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
  cet = CET(*args,**keywords)
  if not ('no-model-data' in keywords):
    cet.model_data()
  if not ('no-model-pid' in keywords):
    cet.model_with_pid(keywords)
