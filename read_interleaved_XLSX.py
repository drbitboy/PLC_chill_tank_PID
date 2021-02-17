# -*- coding: utf-8 -*-
"""
Read XLSX file 'Tank_20_Results_Feb_11-12_2021_R1.xlsx' from

  https://www.plctalk.net/qanda/showthread.php?t=128251

into three numpy arrays:
- relative time;
- Controlled Values (CVs);
- Present (measured) Values (PVs).

For use with script 'SysID SOPDT.py'

Author:  Brian T. Carcich a.k.a. drbitboy
Company:  Latchmoor Services, INC
Initial date:  2021-02-13
"""
import sys
import numpy as np
import pandas as pd

def read_XLSX(path,zero_to_20=False):
  """
  Reads the eXcel file designated by path
  The data must be in the second worksheet (sheet_name==1)
  The worksheet must have a 1-line header
  The first column header must be DataAndTime
  The second column must contain the data values:  CVs and PVs
  The last column must contain 171 for CVs, and contain not 171 for PVs
  The number CVs and PVs must be the same
  The time for each CV must match a times for corresponding PV
  The times must be integral seconds offset from the first time

  """
  ### Read data into Pandas DataFrame
  df = pd.read_excel(path,sheet_name=1).sort_values(by='DateAndTime',inplace=False)
  ### Convert columns 0 (DateAndTime), 1 (data), -1 (CV/PV indicator) to
  ### Numpy array; convert Timestamp column to offsets in ns, then in s,
  ### then all to np.float
  rawarr = df.values[:,[0,1,-1]]
  rawarr[:,0] = (df.DateAndTime.values-df.DateAndTime.values[0])*1e-9
  rawarr = np.array(rawarr,dtype=np.float)
  ### Find CV rows, then PV rows
  iw_cv = np.where(rawarr[:,-1]==171)
  iw_pv = np.where(rawarr[:,-1]!=171)
  ### Test lengths
  assert len(iw_cv[0])==len(iw_pv[0])
  ### Get offset times, ensure whole seconds, ensure CVs' offsets = PVs'
  aTimes = rawarr[iw_cv,0]
  assert 1.0<=np.min(aTimes[0,1:]-aTimes[0,:-1]),'Input data include invalid (duplicate) times'
  assert not [None for rem in aTimes[0] if 0.0!=(rem%1.0)],'Some times are not whole seconds different from others'
  assert np.alltrue(aTimes==rawarr[iw_pv,0]),'Times are not perfectly paired'
  ### Extract and flatten offset times, CVs, rounded PVs
  aTimes = aTimes.flatten()
  CVs = rawarr[iw_cv,1].flatten()
  PVs = np.round(rawarr[iw_pv,1].flatten(),3)
  ### Check if --zero-to-20 fix is needed
  if zero_to_20:
    ### Control valve is opened from 0% to 7ma out of 4-20ma i.e. 3/16
    ### of range on 0% to 1% output of PIDE; assume 1:1 after that
    iw_nonzero = np.where(CVs > 0.9999)
    CVs[iw_nonzero] = CVs[iw_nonzero] + (300./16.)
    rawarr[iw_cv,1] = CVs
  ### Include only rows where PV > 0
  iw = np.where(PVs>0.0)
  ### Return offset times, CVs, rounded PVs
  return aTimes[iw],CVs[iw],PVs[iw]

########################################################################
def massage_XLSX(path,zero_to_20=False):
  """
  Read data using read_XLSX above; remove PVs of zero; merge sections of
  contiguous duplicate data

  """
  aTimes,CVs,PVs = triple= read_XLSX(path,zero_to_20=zero_to_20)
  iw = np.where(PVs>0.0)
  sumt = [0.0]*3
  lastPV,lastCV,firsti,n = -1e32,-1e32,0,0
  for i in range(len(aTimes)):

    aTimei,CVi,PVi = aTimes[i],CVs[i],PVs[i]

    if 0.0 >= PVi:
      if 0==n: firsti = i+1
      continue

    if lastPV!=PVi or lastCV!=CVi:
      if n > 1: aTimes[firsti] /= n
      lastPV,lastCV,firsti,n = PVi,CVi,i,1
      continue

    aTimes[firsti] += aTimei
    PVs[i] = 0.0
    n += 1

    ### End of loop

  if n > 0: aTimes[firsti] /= n

  iw = np.where(PVs > 0.0)
  return aTimes[iw], CVs[iw], PVs[iw]

########################################################################
if "__main__" == __name__:
  """
  Run this file To test the read_XLSX program by itself.
  The path must point to the file you want to read.

  Usage:  python read_interleaved_XLSX.py
          python read_interleaved_XLSX.py ['Tank_20_Results_Feb_11-12_2021_R1.xlsx'] [--convert-to-tsv[ > Tank_data.txt]]
          python read_interleaved_XLSX.py 'Tank....xlsx' [--convert-to-tsv --massage-tank-data[ > Tank_data_massage.txt]]

          N.B. [...] means ... is optional argument(s)
  """
  path = ([s for s in sys.argv[1:] if not s.startswith('--')] + ['Tank_20_Results_Feb_11-12_2021_R1.xlsx'])[0]
  zero_to_20 = '--zero-to-20' in sys.argv[1:]

  if '--massage-tank-data' in sys.argv[1:]:
    aTimes,CVs,PVs = massage_XLSX(path,zero_to_20=zero_to_20)
    sys.stderr.write('Method [massage_XLSX] successfully massaged {1} data from file [{0}]\n'.format(path,len(aTimes)))
  else:
    aTimes,CVs,PVs = read_XLSX(path,zero_to_20=zero_to_20)
    sys.stderr.write('Method [read_XLSX] successfully read {1} data from file [{0}]\n'.format(path,len(aTimes)))

  if '--convert-to-tsv' in sys.argv[1:]:
    for triple in (['"time" "CO" "PV"'.split()]+list(zip(aTimes,CVs,PVs))):
      sys.stdout.write('{0}\t{1}\t{2}\r\n'.format(*triple))
