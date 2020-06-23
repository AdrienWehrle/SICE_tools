# -*- coding: utf-8 -*-
"""

@author: Adrien Wehrlé, Jason E. Box, GEUS (Geological Survey of Denmark and Greenland)


Computation of an empirical Broandband Albedo (BBA) from Top of Atmosphere reflectances (r_TOA), 
further combined planar shortwave broadband albedo values when the latter are below bare ice 
albedo (0.565).

Application of a temporal filtering based on outlier detection modified after Box et al, 2017.

Production of a daily cumulative ("gapless") product (updating pixel values when an area is 
considered cloud free).

"""

import glob
import rasterio
import numpy as np
import os
import pickle
import time
from multiprocessing import Pool, freeze_support


#folder containing SICE outputs
SICE_path='H:/SICE/'
#folder to store outputs
output_path='H:/SICE_PP/'

#list SICE folders of a given year
year=2019
SICE_folders=list(sorted(glob.glob(SICE_path+str(year)+'*/')))

#keep only folder where needed r_TOAs and planar BBA are available
SICE_folders_av=[folder for folder in SICE_folders if os.path.isfile(folder+'albedo_bb_planar_sw.tif') and
                 os.path.isfile(folder+'r_TOA_01.tif') and os.path.isfile(folder+'r_TOA_06.tif') and
                 os.path.isfile(folder+'r_TOA_17.tif') and os.path.isfile(folder+'r_TOA_21.tif')]

#list SICE planar broadband albedo
planar_BBA_files=[path+'albedo_bb_planar_sw.tif' for path in SICE_folders_av]

#load an example of raster 
ex=rasterio.open(planar_BBA_files[0]).read(1)

#load profile to further save outputs 
profile=rasterio.open(planar_BBA_files[0]).profile

#parameters for temporal filtering
deviation_threshold=0.2 #compute temporal average for deviations below deviation_threshold
rolling_window=10 #center value +-rolling_window days (11 days)
limit_valid_days=4 #need at least limit_valid_days valid days to compute temporal average 


def SICE_processing(k):
    
    '''
    
    Compute an empirical Broandband Albedo (empirical_BBA), combine with SICE planar shortwave 
    broadband albedo (planar_BBA) when below bare ice albedo (0.565) and apply a temporal 
    filtering based on outlier detection.
    
    
    INPUTS:
        k: iterator from zero to the number of available SICE folders [int]
        
    OUTPUTS:
        filtered_BBAs[date]: filtered broadband albedo combination at the date
                             associated with the iterator k, stored in filtered_BBAs 
                             dictionnary [array]
        
    '''
    
    #load several rasters into a 3D list
    def load_rasters(files):
        data=[rasterio.open(file).read(1) for file in files]
        return data
    
    #do not compute around boundaries 
    if k>rolling_window/2 and k<len(planar_BBA_files)-rolling_window/2:
        
        #initialize 3D matrix 
        BBAs_window=np.zeros((np.shape(ex)[0], np.shape(ex)[1], rolling_window+1))
        BBAs_window[:]=np.nan
        
        #compute empirical albedo rasters, combine with planar albedo and stack resulting rasters 
        #Kwithin rolling_window in 3D matrix 
        for w,j in enumerate(range(k-int(rolling_window/2), k+int(rolling_window/2+1))):
            
            r_TOA_files=[SICE_folders_av[k]+var for var in ['r_TOA_01.tif','r_TOA_06.tif','r_TOA_17.tif',
                                                            'r_TOA_21.tif']]
            
            r_TOAs=load_rasters(r_TOA_files)
            
            r_TOAs_combination=np.nanmean(r_TOAs,axis=0)
            
            empirical_BBA=0.901*r_TOAs_combination+0.124
            
            planar_BBA=rasterio.open(planar_BBA_files[j]).read(1)
            
            planar_BBA[(planar_BBA<0)&(planar_BBA>1)]=np.nan
            
            #integrate empirical_BBA when planar_BBA values are below bare ice albedo
            planar_BBA[planar_BBA<=0.565]=empirical_BBA[planar_BBA<=0.565]
            BBAs_window[:,:,w]=planar_BBA
        
        
        #compute deviations for each pixel along rolling_window
        deviations=np.abs(BBAs_window-np.nanmedian(BBAs_window,2,keepdims=True))\
                          /np.nanmedian(BBAs_window,2,keepdims=True)
        
        #count valid days for each pixel along rolling_window
        nb_valid_days=np.sum(deviations<deviation_threshold, axis=2)
        
        #exclude invalid cases
        BBAs_window[deviations>deviation_threshold]=np.nan 
        
        #store albedo pixel in filtered_BBAs if nb_valid_days is above limit_valid_days
        date=planar_BBA_files[k].split(os.sep)[-2]
        filtered_BBA=np.zeros((np.shape(ex)[0],np.shape(ex)[1])); filtered_BBA[:]=np.nan
        filtered_BBA[nb_valid_days>limit_valid_days]=np.nanmean(BBAs_window,axis=2)[nb_valid_days>limit_valid_days]
    
    else:
        filtered_BBA=None; date=None
    
    print(k,'/',len(planar_BBA_files))
    
    
    return filtered_BBA, date
    

import warnings
warnings.filterwarnings("ignore")

if __name__ == '__main__':
    
    #initialize a dictionnary thereafter containing dates as keys
    #and daily filtered BBAs as values
    filtered_BBAs={}
    
    #computer cores to use for multiprocessing
    nb_cores=5
    
    #save start time to compute processing time
    start_time = time.time()
    start_local_time = time.ctime(start_time)
    print('SICE_processing...')

    freeze_support()
    with Pool(nb_cores) as p:
        for f_BBA, date in p.map(SICE_processing, list(range(0,len(SICE_folders_av)))):
            if f_BBA is not None:
                filtered_BBAs[date]=f_BBA
            
    print(list(filtered_BBAs.keys()))
                
    end_time = time.time()
    end_local_time = time.ctime(end_time)
    processing_time=(end_time - start_time)/60
    print("--- Processing time: %s minutes ---" % processing_time)
    print("--- Start time: %s ---" % start_local_time)
    print("--- End time: %s ---" % end_local_time)  
        
        
    #save filtered_BBAs dictionnary in a pickle file
    file_name='H:/SICE_filtered_BBA_4_02_10rm'+str(year)+'.pkl'
    f = open(file_name,'wb')
    pickle.dump(filtered_BBAs,f)
    f.close()  
    #how to load a pkl file 
    # with open(file_name, 'rb') as f:
    #     filtered_BBAs = pickle.load(f)  
    
    #use first month average as initialization of the gapless product
    fm=list(filtered_BBAs.keys())[0].split('-')[1]
    fm_dates=[key for key in list(filtered_BBAs.keys()) 
              if key.split('-')[1]==fm]
    
    fm_BBA=np.zeros((np.shape(ex)[0], np.shape(ex)[1], len(fm_dates)))
    
    for op,date in enumerate(fm_dates):
        
        fm_BBA[:,:,op]=filtered_BBAs[date]
        
    BBA_initialization=np.nanmean(fm_BBA, axis=2)
    
    #initialize a dictionnary thereafter containing dates as keys
    #and daily cumulative filtered BBAs as values
    filtered_BBAs_cumulative={}
    
    #gapfilling forwards
    for i,key in enumerate(filtered_BBAs):
        
        if i==0:
            filtered_BBAs_cumulative[key]=BBA_initialization
            valid=[(filtered_BBAs[key]>0)&(filtered_BBAs[key]<1)] 
            filtered_BBAs_cumulative[key][valid]=filtered_BBAs[key][valid]
            cuml=filtered_BBAs_cumulative[key]
            
        else:
            valid=[(filtered_BBAs[key]>0)&(filtered_BBAs[key]<1)] 
            cuml[valid]=filtered_BBAs[key][valid]
            filtered_BBAs_cumulative[key]=cuml
        
        with rasterio.open(output_path+key+'.tif', 'w', **profile) as dst:
            dst.write(filtered_BBAs_cumulative[key].astype(np.float32), 1)
