import os
import sys

class PID:
  """
Implement Dependent Gains Form* of Proportional-Integral-Derivative
controller

* Cf. https://literature.rockwellautomation.com/idc/groups/literature/documents/wp/logix-wp008_-en-p.pdf

[PVlo:PVhi] will be scaled and clampled to [0:100] internally, and the
formula applied to that range.  The CV calculated by the formula will be
clamped to [0:100], and then scaled to [CVlo:CVhi], so there will be no
windup beyond [CVlo:CVhi]

  """
  def __init__(self
              ,Kc,Ti,Td             ### Ratio, Minutes, Minutes
              ,CVlast=50.0          ### % of CV range
              ,Updatetime=45.0      ### Seconds
              ,Deadband=0.01        ### % of PV range (not yet implemented)
              ,Direct=True          ### E(rror) = PV - SP; CV will increase in response to increasing PV
                                    ### Direct=False => E(rror) = SP - PV;
              ,Auto=True
              ,PVlo=0.0,PVhi=100.0  ### See comment in self.__doc__
              ,CVlo=0.0,CVhi=100.0 
              ):
    """Store inputs"""

    (self.Kc,self.Ti,self.Td
    ,self.CVlast,self.Updatetime,self.Deadband
    ,self.Direct,self.Auto
    ,) = (Kc,Ti,Td
         ,CVlast,Updatetime,Deadband
         ,Direct,Auto
         ,)

    ### Initialize empty past PVs list for Td, last error for Kc, for
    ### bumpless transfer
    self.lastPVs,self.lastError = [],None 

    ### Setup scaling and limits
    self.set_PVlims(PVlo,PVhi)
    self.set_CVlims(CVlo,CVhi)


  def control(self,PVexternal,SPexternal):
    """Execute one update of control algorithm"""

    ### Ingest external Present (measured) Value and SetPoint
    PVinternal,SPinternal = map(self.ingestPV,(PVexternal,SPexternal,))

    ### Calculate current error
    if self.Direct: err = PVinternal - SPinternal
    else          : err = SPinternal - PVinternal

    ### Duplicate error for missing last error, for bumpless transfer
    ### Duplicate PV as .lastPVs, for Td bumpless transfer
    if None is self.lastError: self.lastError = err
    while len(self.lastPVs) < 2: self.lastPVs.append(PVinternal)

    ### Calculate Td deltar-delta-error term
    dEterm = PVinternal + self.lastPVs[-2] - (2.0 * self.lastPVs[-1])

    ### Calculate change in CV, internal scaling
    deltaCV = self.Kc * ( (err - self.lastError)                      #P
                        + (err * self.Updatetime / (60.0 * self.Ti))  #I
                        + (60.0 * self.Td * dEterm / self.Updatetime) #D
                        )

    ### Save .lastPVs and last error
    self.lastPVs,self.lastError = [self.lastPVs[-1],PVinternal],err

    ### Calculate new CV, save as .CVlast
    self.CVlast =  self.emitCV(deltaCV)
    return self.CVlast

  def ingestPV(self,PVexternal):
    """
    Ingest PV from extenal units to internal units, clamp as needed

    """
    if   PVexternal > self.PVmax: clampPV = self.PVmax
    elif PVexternal < self.PVmin: clampPV = self.PVmin
    else                        : clampPV = PVexternal
    return (clampPV-self.PVlo) / self.PVmag

  def emitCV(self,deltaCV):
    """
    Scale internal change in CV to external units,
    add to last CV, scale as needed

    """
    CVexternal =  self.CVlast + (deltaCV * self.CVmag)
    if CVexternal > self.CVmax: return self.CVmax
    if CVexternal < self.CVmin: return self.CVmin
    return CVexternal

  def get_minmax(self,lo,hi): return lo,hi,(hi-lo)/100.0,(lo<hi) and (lo,hi,) or (hi,lo,)

  def set_CVlims(self,CVlo,CVhi):
    self.CVlo,self.CVhi,self.CVmag,(self.CVmin,self.CVmax,) = self.get_minmax(CVlo,CVhi)

  def set_PVlims(self,PVlo,PVhi):
    self.PVlo,self.PVhi,self.PVmag,(self.PVmin,self.PVmax,) = self.get_minmax(PVlo,PVhi)
