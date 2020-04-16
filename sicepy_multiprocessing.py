# -*- coding: utf-8 -*-
"""

@author: Adrien Wehrlé, GEUS (Geological Survey of Denmark and Greenland)

Run sice.py using multiprocessing with the nb_cores available.
Multiprocessing is used over years if only one day per year, over days of the 
different years otherwise.  
If two days are given, range inbetween day1 and day2. If more than two days,
given days are run. 

"""

import os
import sys
import subprocess
import numpy as np
import multiprocessing
from multiprocessing import Pool

nb_cores=multiprocessing.cpu_count()

mosaic_root=(sys.argv)[1]
doys_years=(sys.argv)[2:]

doys=[]
[doys.append(np.int(i)) for i in doys_years if len(i)==3]
years=[]
[years.append(np.int(i)) for i in doys_years if len(i)==4]


def sicepy_multiprocessing(k):
    
    if len(doys)==1:
        date=subprocess.check_output('date -d "'+str(years[k])+'-01-01 +$(('+str(doy)+'-1 ))\
                                              days" "+%Y-%m-%d"', shell=True)
    else:
        date=subprocess.check_output('date -d "'+str(year)+'-01-01 +$(('+str(dates[k])+'-1 ))\
                                              days" "+%Y-%m-%d"', shell=True)

    os.system('./sice.py '+mosaic_root+'/'+date.decode("utf-8"))


# one day: multiprocessing over years
if len(doys)==1: 
    
    doy=doys[0]
    op=len(years)
    
    if __name__ == '__main__':
        with Pool(nb_cores) as p:
            p.map(sicepy_multiprocessing, np.arange(0,op)) 


else:
    
    # two days: multiprocessing over days from day1 to day2.
    if len(doys)==2:
        dates=list(range(doys[0],doys[1]+1))
        op=len(dates)
        
    # more than two days: multiprocessing over days for the given dates.  
    elif len(doys)>2:
        dates=doys
        op=len(dates)
        
    for year in years:
        if __name__ == '__main__':
            with Pool(nb_cores) as p:
                p.map(sicepy_multiprocessing, np.arange(0,op))   
