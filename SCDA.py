# -*- coding: utf-8 -*-
"""

@author: Adrien Wehrlé, GEUS (Geological Survey of Denmark and Greenland)

Implementation of the Simple Cloud Detection Algorithm (SCDA) v2.0
using SLSTR bands, described in Fig. 5 of METSÄMÄKI et al, 2015.

METSÄMÄKI, Sari, PULLIAINEN, Jouni, SALMINEN, Miia, et al. Introduction 
to GlobSnow Snow Extent products with considerations for accuracy assessment. 
Remote Sensing of Environment, 2015, vol. 156, p. 96-108.

v1.4 is implemented based on GlobSnow "Technical note 2 Cloud Detection
Algorithm SCDA".
https://www.globsnow.info/docs/GlobSnow_technical_note2_scda_final_release.pdf

The original syntax has been preserved to easily link back to the description
of the algorithm.


INPUTS:
    inpath: Path to the folder of a given date containing extracted scenes
                in .tif format. [string]
    multi_proc: run functions by multiprocessing using the nb_cores available
                to drastically decrease computation time.
            
OUTPUTS:
        {inpath}/NDSI.tif: Normalized Difference Snow Index (NDSI) in a 
                           .tif file, stored in {inpath}. [.tif]
        {inpath}/SCDA_v20.tif: Simple Cloud Detection Algorithm (SCDA) v2.0
                               results in a .tif file, stored in {inpath}. [.tif]
        {inpath}/SCDA_v14.tif: Simple Cloud Detection Algorithm (SCDA) v1.4
                               results in a .tif file, stored in {inpath}. [.tif]
    

"""

import numpy as np
from numpy import asarray as ar
import rasterio 
import argparse
import os
import time
import multiprocessing
from multiprocessing import Pool

multi_proc=False

parser = argparse.ArgumentParser()
parser.add_argument('inpath')
args = parser.parse_args()


def radiometric_calibration(R16,scene,inpath=args.inpath):
    '''
    Sentinel-3 Product Notice – SLSTR:
    "Based on the analysis performed to-date, a recommendation has been put forward to users to
    adjust the S5 and S6 reflectances by factors of 1.12 and 1.20 respectively in the nadir view and
    1.15 and 1.26 in the oblique view. Uncertainty estimates on these differences are still to be
    evaluated and comparisons with other techniques have yet to be included."
    
    INPUTS:
        R16: Dataset reader for Top of Atmosphere (TOA) reflectance channel S5.
             Central wavelengths at 1.6um. [rasterio.io.DatasetReader]
        scene: Scene on which to compute SCDA. [string]
        
    OUTPUTS:
        {inpath}/S5_reflectance_an_rc_x.tif: Adjusted Top of Atmosphere (TOA)
                                             reflectance for channel S5.
    '''
    
    profile_R16=R16.profile
    factor=1.12
    R16_data=R16.read(1)
    R16_rc=R16_data*factor
    
    with rasterio.open(inpath+os.sep+scene+os.sep+'S5_reflectance_an_rc_x.tif','w',**profile_R16) as dst:
        dst.write(R16_rc, 1)
    
    
    


    
def SCDA_v20(R550,R16,BT37,BT11,BT12,profile,scene,inpath=args.inpath, SICE_toolchain=True):
    '''
    
    INPUTS:
        inpath: Path to the folder of a given date containing extracted scenes
                in .tif format. [string]
        SICE_toolchain: if True: cloud=255, clear=1
                        if False: cloud=1, clear=0
        profile: Profile to save outputs. [rasterio.profiles.Profile]
        scene: Scene on which to compute the SCDA. [string]
        R550, R16: Top of Atmosphere (TOA) reflectances for channels S1 and S5.
                   Central wavelengths at 550nm and 1.6um. [arrays]
        BT37, BT11, BT12: Gridded pixel Brightness Temperatures (BT) for channels 
                          S7, S8 and S9 (1km TIR grid, nadir view). Central 
                          wavelengths at 3.7, 11 and 12 um. [arrays]
              
    OUTPUTS:
        {inpath}/NDSI.tif: Normalized Difference Snow Index (NDSI) in a 
                           .tif file, stored in {inpath}. [.tif]
        {inpath}/SCDA.tif: Simple Cloud Detection Algorithm (SCDA) results 
                           in a .tif file, stored in {inpath}. 
                           clouds=1, clear=0 [.tif]
         
    '''
    
    #determining the NDSI, needed for the cloud detection
    NDSI=(R550-R16)/(R550+R16)
    with rasterio.open(inpath+os.sep+scene+os.sep+'NDSI.tif','w',**profile) as dst:
        dst.write(NDSI, 1)
    
    #initializing thresholds
    base=np.empty((R550.shape[0],R550.shape[1]))
    THR=base.copy()
    THR[:]=np.nan
    THRmax=base.copy()
    THRmax[:]=-5.5 
    S=base.copy()
    S[:]=1.1
    
    #tests 1 to 5, only based on inputs
    t1=ar(R550>0.30)*ar(NDSI/R550<0.8)*ar(BT12<=290)
    t2=ar(BT11-BT37<-13)*ar(R550>0.15)*ar(NDSI >= -0.30)\
       *ar(R16>0.10)*ar(BT12<=293)
    t3=ar(BT11-BT37<-30)
    t4=ar(R550<0.75)*ar(BT12>265)
    t5=ar(R550>0.75)
    
    
    cloud_detection=t1
    cloud_detection[cloud_detection==False]=t2[cloud_detection==False]
    cloud_detection[cloud_detection==False]=t3[cloud_detection==False]
    
    THR1=0.5*BT12-133
    
    THRmax[t4==False]=-8
    THR=np.minimum(THR1,THRmax)
    S[t5==False]=1.5
    
    #test 6, based on fluctuating thresholds
    t6=ar(BT11-BT37<THR)*ar(NDSI/R550<S)*ar((NDSI>=-0.02) & (NDSI<=0.75))\
       *ar(BT12<=270)*ar(R550>0.18)

    cloud_detection[cloud_detection==False]=t6[cloud_detection==False]
    
    if SICE_toolchain:
        cloud_detection[cloud_detection==True]=255
        cloud_detection[cloud_detection==False]=1
    
    #writing results
    profile_cloud_detection=profile.copy()
    profile_cloud_detection.update(dtype=rasterio.int16)
    with rasterio.open(inpath+os.sep+scene+os.sep+'SCDA_v20.tif','w',**profile_cloud_detection) as dst:
        dst.write(cloud_detection.astype(np.int16), 1)
    
    return cloud_detection, NDSI




def SCDA_v14(R550,R16,BT37,BT11,BT12,NDSI,profile,scene,inpath=args.inpath,NDSI_cp=False, SICE_toolchain=True):
    '''
    
    INPUTS:
        inpath: Path to the folder of a given date containing extracted scenes
                in .tif format. [string]
        SICE_toolchain: if True: cloud=255, clear=1
                        if False: cloud=1, clear=0
        profile: Profile to save outputs. [rasterio.profiles.Profile]
        scene: Scene on which to compute SCDA. [string]
        R550, R16: Top of Atmosphere (TOA) reflectances for channels S1 and S5.
                   Central wavelengths at 550nm and 1.6um. [arrays]
        BT37, BT11, BT12: Gridded pixel Brightness Temperatures (BT) for channels 
                          S7, S8 and S9 (1km TIR grid, nadir view). Central 
                          wavelengths at 3.7, 11 and 12 um. [arrays]
        NDSI: Normalized Difference Snow Index (NDSI) computed by SCDA_v20.
              If only running SCDA_v14, set NDSI_cp to True [array|boolean]
              
    OUTPUTS:
        if NDSI_cp set to False: 
            {inpath}/NDSI.tif: Normalized Difference Snow Index (NDSI) in a 
                               .tif file, stored in {inpath}. [.tif]
        {inpath}/SCDA.tif: Simple Cloud Detection Algorithm (SCDA) results 
                           in a .tif file, stored in {inpath}. 
                           clouds=1, clear=0 [.tif]
         
    '''
    
    if NDSI_cp==True:
        #determining the NDSI, needed for the cloud detection
        NDSI=(R550-R16)/(R550+R16)
        with rasterio.open(inpath+os.sep+scene+os.sep+'NDSI.tif','w',**profile) as dst:
            dst.write(NDSI, 1)
        
    diff=BT11-BT37
    diff_threshold=0.5*BT12-131
    
    diff_threshold[diff_threshold>-6]=-6
    
    #tests 1 and 2, only based on inputs
    t1=ar(diff<=diff_threshold)*ar(BT12<287)*ar((NDSI>-0.2) & (NDSI<0.69))\
       *ar(R550>20)
    t2=ar(diff<-3)*ar(diff>diff_threshold)*ar(BT12<287)*ar((NDSI>-0.05) & (NDSI<0.6))\
       *ar(R550>20)*ar(NDSI*100<1.1*R550)
       
    cloud_detection=t1
    cloud_detection[cloud_detection==False]=t2[cloud_detection==False]
    
    if SICE_toolchain:
        cloud_detection[cloud_detection==True]=255
        cloud_detection[cloud_detection==False]=1
    
    #writing results
    profile_cloud_detection=profile.copy()
    profile_cloud_detection.update(dtype=rasterio.int16)
    with rasterio.open(inpath+os.sep+scene+os.sep+'SCDA_v14.tif','w',**profile_cloud_detection) as dst:
        dst.write(cloud_detection.astype(np.int16), 1)
    
    
    return cloud_detection





#listing scenes for a given date
scenes=os.listdir(args.inpath)

if multi_proc==False:
    for i,scene in enumerate(scenes):
        
        #saving profile metadata only for the first iteration
        profile=rasterio.open(args.inpath+os.sep+scene+os.sep+'S1_reflectance_an_x.tif').profile
        
        #calibrating R16
        R16=rasterio.open(args.inpath+os.sep+scene+os.sep+'S5_reflectance_an_x.tif')
        radiometric_calibration(R16=R16,scene=scene)
        
        #loading inputs
        R550=rasterio.open(args.inpath+os.sep+scene+os.sep+'S1_reflectance_an_x.tif').read(1)
        R16=rasterio.open(args.inpath+os.sep+scene+os.sep+'S5_reflectance_an_rc_x.tif').read(1)
        BT37=rasterio.open(args.inpath+os.sep+scene+os.sep+'S7_BT_an_x.tif').read(1)
        BT11=rasterio.open(args.inpath+os.sep+scene+os.sep+'S8_BT_an_x.tif').read(1)
        BT12=rasterio.open(args.inpath+os.sep+scene+os.sep+'S9_BT_an_x.tif').read(1)
        
        #running SCDA v2.0 and v1.4
        cd,NDSI=SCDA_v20(R550=R550,R16=R16,BT37=BT37,BT11=BT11,BT12=BT12,scene=scene,profile=profile)
        SCDA_v14(R550=R550,R16=R16,BT37=BT37,BT11=BT11,BT12=BT12,NDSI=NDSI,scene=scene,profile=profile)
        
        print('%s: done' % scene)
        
      
        
if multi_proc==True:
    
    def multiproc_SCDA(k):
        #saving profile metadata only for the first iteration
        if k==0:
            profile=rasterio.open(args.inpath+os.sep+scenes[k]+os.sep+'S1_reflectance_an_x.tif').profile
        
        #calibrating R16
        R16=rasterio.open(args.inpath+os.sep+scenes[k]+os.sep+'S5_reflectance_an_x.tif')
        radiometric_calibration(R16=R16,scene=scenes[k])
        
        #loading inputs
        R550=rasterio.open(args.inpath+os.sep+scenes[k]+os.sep+'S1_reflectance_an_x.tif').read(1)
        R16=rasterio.open(args.inpath+os.sep+scenes[k]+os.sep+'S5_reflectance_an_rc_x.tif').read(1)
        BT37=rasterio.open(args.inpath+os.sep+scenes[k]+os.sep+'S7_BT_an_x.tif').read(1)
        BT11=rasterio.open(args.inpath+os.sep+scenes[k]+os.sep+'S8_BT_an_x.tif').read(1)
        BT12=rasterio.open(args.inpath+os.sep+scenes[k]+os.sep+'S9_BT_an_x.tif').read(1)
        
        #running SCDA v2.0 and v1.4
        cd,NDSI=SCDA_v20(R550=R550,R16=R16,BT37=BT37,BT11=BT11,BT12=BT12,scene=scenes[k],profile=profile)
        SCDA_v14(R550=R550,R16=R16,BT37=BT37,BT11=BT11,BT12=BT12,NDSI=NDSI,scene=scenes[k],profile=profile)
        

    #multiprocessing run    
    nb_cores=multiprocessing.cpu_count()
    start_time = time.time()
    
    if __name__ == '__main__':
        with Pool(nb_cores) as p:
            p.map(multiproc_SCDA, list(range(0,len(scenes))))

    print("--- %s seconds ---" % (time.time() - start_time))
    
