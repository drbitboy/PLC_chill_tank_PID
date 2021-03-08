# -*- coding: utf-8 -*-
"""
Created on Thu Aug 10 13:59:32 2017

@author: Peter Nachtwey
Delta Computer Systems, Inc.
"""

import numpy as np
import csv


def readCSV(path):
    """ Reads the CSV file designated by the path.
        ch is the deliminator. It could be a comma, tab or spaces 
        The file must have a 1 line header that is ignored.
        The data must be in three columns of time, control and actual """
    #with open(path, newline='') as csvfile:
    with open(path) as csvfile:
        dialect = csv.Sniffer().sniff(csvfile.read(1024), delimiters=',\t ')
        csvfile.seek(0)
        bHdr = csv.Sniffer().has_header(csvfile.read(1024))        
        csvfile.seek(0)
        readCSV = csv.reader(csvfile, dialect)
        if bHdr:
            header = next(readCSV, None)        # the header is ignored
        lTime = []                              # define empty lists
        lAct = []                               # use dictionary for dynamic
        lCtrl = []                              # lists
        for row in readCSV:
            # row = [time, control, actual,.......]
            lTime.append(float(row[0]))
            lCtrl.append(float(row[1]))
            lAct.append(float(row[2]))
    csvfile.close()
    aTime = np.array(lTime)             # convert from lists to np.array
    aAct = np.array(lAct)
    aControl = np.array(lCtrl)
    return [aTime, aControl, aAct]      # return a list of three np.arrays


if __name__ == "__main__":
    """ Run this file To test the readCSV program by itself.
        The path must point to the file you want to read.
        The delminantor character must be set correctly.
        Type the arrays to verify the data is read correctly """
    path="hotrod.txt"
    aTime, aControl, aAct = readCSV(path)
