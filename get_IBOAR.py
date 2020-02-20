# -*- coding: utf-8 -*-
"""
Created on Fri Jan 17 08:45:17 2020

@author: Adrien Wehrlé, GEUS (Geological Survey of Denmark and Greenland)


Computes the Intrinsic Bottom of Atmosphere Reflectance (IBOAR) for a given scene
and given bands. ArcticDEM derived slopes and aspects are used after resampling 
and clipping.

Functions are first initialized and then run at the end of the code.


INPUTS:
    run_command_line: run the code from the command line (using an argument parser) [boolean]
    time_it: set to True to print processing time [boolean]
    inpath: path to the folder containing the desired S3 scene processed using the 
            2nd step of SICE processing pipeline (https://github.com/mankoff/SICE/) [string]
    inpath_adem: path to the folder containing regional ArcticDEM derived 
                 slopes and aspects [string]
    region: region over which the toolchain is run [string]
    slope_thres: slope threshold in degrees to create slope_flag. Default 
                     is set to 15° based on the "small slope approximation" 
                     (Picard et al, 2020) [int]
    outpath: path where to save {var}_eff.tif [string]
    
    WARNING: SZA.tif, OZA.tif, SAA.tif and rBRR_{band_num}.tif are needed 
             in each scene folder for the algorithm to run.
             
    
        
OUTPUTS:
    for a given scene:
        slope.tif: tiff file containing the slope [.tif]
        slope_flag.tif: tiff file containing slope_flag based on the "small slope
                        approximation" (Picard et al, 2020) [.tif]
        aspect.tif: tiff file containing the effective angles [.tif]
        SZA_eff.tif: tiff file containing the effective solar zenith angle [.tif]
        OZA_eff.tif: tiff file containing the viewing solar zenith angle [.tif]
        IBOAR_{band_num}.tif: tiff file containing the effective angles for each
                              band_num [.tif] 
        
"""

import numpy as np
import sys
import rasterio
import glob
import os
import argparse
from osgeo import gdal, gdalconst
import time

time_it=True
run_command_line=False

if time_it==True:
    start_time = time.time()

if run_command_line==True:
    
    parser = argparse.ArgumentParser()
    parser.add_argument('inpath')
    parser.add_argument('inpath_dem')
    
    args = parser.parse_args()
    
    
if run_command_line==False:
    
    var='SZA'
    inpath='/srv/home/8675309/AW/20190802/'
    inpath_adem='/srv/home/8675309/AW/'
    region='Greenland'
    slope_thres=15
    outpath='/srv/home/8675309/AW/'
    



def get_effective_angles(var=var,inpath=inpath,inpath_adem=inpath_adem,region=region,
                         slope_thres=slope_thres,outpath=outpath):
    
    '''
    
    Determines effective solar/viewing angles to compute the Intrinsic BOA Reflectance (IBOAR).
    
    INPUTS:
        var: name of the variable to compute [string]
        inpath: path to the folder containing the variables ({var} and SAA needed) [string]
        inpath_adem: path to the folder containing regional ArcticDEM derived 
                     slopes and aspects [string]
        region: region over which the toolchain is run [string]
        slope_thres: slope threshold in degrees to create slope_flag. Default 
                     is set to 15° based on the "small slope approximation" 
                     (Picard et al, 2020). 1 for slope<=slope_thres, 
                     255 (no data) for slope>slope_thres [int]
        outpath: path where to save {var}_eff.tif [string]
    
    OUTPUTS:
        {var}_eff: effective angles [array]
        slope_flag: slope mask based on the "small slope approximation" 
                     (Picard et al, 2020). 1 for slope<=threshold, 
                     255 (no data) for slope>threshold [array]
        {var}_eff.tif: tiff file containing the effective angles [.tif] 
        if variable is set to SZA:
            slope.tif: tiff file containing the slope [.tif]
            slope_flag.tif: tiff file containing the slope_flag [.tif] 
            aspect.tif: tiff file containing the slope aspect [.tif]
        
    '''
    
    #loading variables
    try:
        angle_name=var+'.tif'
        angle=rasterio.open(inpath+var+'.tif').read(1)
    except:
        print('ERROR: %s is missing' %angle_name)
        return
    try:
        saa=rasterio.open(inpath+'SAA.tif').read(1)
    except:
        print('ERROR: SAA.tif is missing')
        return
    
    
    
    def resample_clip_adem(var,inpath=inpath,inpath_adem=inpath_adem,outpath=outpath,reg=region):
        '''
        
        Resamples and clips ArcticDEM derived slopes and aspects to match S3Snow
        outputs.
        
        INPUTS:
            var: name of the variable to compute ("slope" or "aspect") [string]
            inpath: path to the folder containing the variables (var, height and saa needed) [string]
            inpath_adem: path to the folder containing regional ArcticDEM derived 
                         slopes and aspects [string]
            outpath: path where to save slope.tif and aspect.tif [string]
                         
        OUTPUTS: 
            if var is set to slope: 
                {outpath}/slope.tif: Resampled and clipped ArcticDEM derived slopes [.tif]
            if var is set to slope: 
                {outpath}/aspect.tif: Resampled and clipped ArcticDEM derived aspects [.tif]
        
        '''
            
        #source
        src_filename = inpath_adem+reg+'_arcticdem_'+var+'.tif'
        src = gdal.Open(src_filename, gdalconst.GA_ReadOnly)
        src_proj = src.GetProjection()
        src_geotrans = src.GetGeoTransform()
        
        #raster to match
        match_filename = inpath+angle_name
        match_ds = gdal.Open(match_filename, gdalconst.GA_ReadOnly)
        match_proj = match_ds.GetProjection()
        match_geotrans = match_ds.GetGeoTransform()
        wide = match_ds.RasterXSize
        high = match_ds.RasterYSize
        
        #output/destination
        dst_filename = inpath+var+'.tif'
        dst = gdal.GetDriverByName('Gtiff').Create(dst_filename, wide, high, 1, gdalconst.GDT_Float32)
        dst.SetGeoTransform( match_geotrans )
        dst.SetProjection( match_proj)
        
        #run
        gdal.ReprojectImage(src, dst, src_proj, match_proj, gdalconst.GRA_NearestNeighbour)
        
    
    #running resample_clip_adem()
    resample_clip_adem(var='slope')
    resample_clip_adem(var='aspect')
    
    #loading slope and aspect
    slope=rasterio.open(inpath+'slope.tif').read(1)
    aspect=rasterio.open(inpath+'aspect.tif').read(1)
    
    
    #creating a flag based on the "small slope approximation" 
    slope_flag=slope.copy()
    slope_flag[np.where(slope<=slope_thres)]=1
    slope_flag[np.where(slope>slope_thres)]=255
    
    #converting slope, aspect, angle and saa to radians
    angle_rad = np.deg2rad(angle)
    saa_rad = np.deg2rad(saa)
    slope_rad = np.deg2rad(slope)
    aspect_rad = np.deg2rad(aspect)
    
    #calculating effective angle
    mu = np.cos(angle_rad) * np.cos(slope_rad) + np.sin(angle_rad) * np.sin(slope_rad) * \
               np.cos(saa_rad - aspect_rad)
               
    eff = np.arccos(mu)
    angle_eff=np.rad2deg(eff)

    #loading initial metadata to save the output
    profile=rasterio.open(inpath+var+'.tif','r').profile
    angle_eff=np.nan_to_num(angle_eff) #nan no data don't pass
    profile.update(nodata=0)
    
    #writing the output
    output_filename=outpath+var+'_eff'+'.tif'
    with rasterio.open(output_filename, 'w', **profile) as dst:
        dst.write(angle_eff, 1)
    
    #writing slope_flag 
    profile.update(nodata=255)
    slope_flag_filename=outpath+'slope_flag_'+str(slope_thres)+'_degrees.tif'
    with rasterio.open(slope_flag_filename, 'w', **profile) as dst:
        dst.write(slope_flag, 1)   
    
    #returning slope, aspect and slope flag only for SZA (only once)
    if var=='SZA':
        return angle_eff, slope, aspect,slope_flag
    
    if var=='OZA':
        return angle_eff






def get_IBOAR(slope,aspect,slope_flag,inpath=inpath,outpath=outpath):
    '''
    
    Determines the Intrinsic Bottom of Atmosphere Reflectance (IBOAR) for given bands 
    as inputs of Alexander Kokhanovsky's algorithm.
    
    INPUTS:
        slope: slope raster [array]
        aspect: aspect of the slope raster [array]
        slope_flag: slope mask based on the "small slope approximation" (Picard et al, 2020). 
                    1 for slope<=threshold, 255 (no data) for slope>threshold [array]
        inpath: path to the folder containing the variables (rBRR and SAA needed) [string]
        outpath: path where to save R_slope_{band}.tif [string]
    
    OUTPUTS:
        IBOAR_{band_num}.tif: tiff file containing the effective angles for each
                              band_num [.tif] 
                              
    '''
    
    #loading solar and viewing zenith angles (flat)
    sza=rasterio.open(inpath+'SZA.tif').read(1)
    oza=rasterio.open(inpath+'OZA.tif').read(1)
    
    #listing available BRR bands
    BRRs_paths=list(np.sort(glob.glob(inpath+'rBRR*')))
    if len(BRRs_paths)==0:
        print('ERROR: no rBRR_XX.tif files')
        return
    
    #loading solar azimuth angle (flat)
    saa_io=rasterio.open(inpath+'SAA.tif')
    profile=saa_io.profile #saving profile as base for IBOAR file
    saa=saa_io.read(1)
    
    
    #computing IBOAR for each available band
    for i,brr in enumerate(BRRs_paths):
        
        #loading BOAR (flat)
        boar=rasterio.open(brr).read(1)
        
        #computing iboar
        mu0=np.cos(np.deg2rad(sza))
        mu=np.cos(np.deg2rad(oza))
        mu0_ov=mu0*np.cos(np.deg2rad(slope))+np.sin(np.deg2rad(sza))\
            *np.sin(np.deg2rad(slope))*np.cos(np.deg2rad(saa)-np.deg2rad(aspect))
        
        iboar=boar*mu0/mu0_ov
        
        #masking iboar with slope_flag
        iboar[slope_flag==255]=255
        
        #saving band number
        band_num=BRRs_paths[i].split(os.sep)[-1].split('.')[0][-2:]
        
        #writing IBOAR_{band_num} in a tif
        profile.update(nodata=255)
        with rasterio.open(outpath+'IBOAR_'+band_num+'.tif', 'w', **profile) as dst:
            dst.write(iboar, 1)
 




        
#running the routine for the desired scene
            
if run_command_line==True:    
    #running get_effective_angles() for SZA and OZA
    try:
        SZA_eff, slope, aspect,slope_flag=get_effective_angles('SZA',inpath=args.inpath)
    except:
        print('ERROR: get_effective_angles() did not completed, see above')
        sys.exit()
    try:
        OZA_eff=get_effective_angles('OZA',inpath=args.inpath)
    except:
        print('ERROR: get_effective_angles() did not completed, see above')
        sys.exit()
    
    
    #running get_IBOAR for IBOAR at a given band
    try:
        get_IBOAR(slope,aspect,slope_flag,inpath=args.inpath)
    except:
        print('ERROR: get_IBOAR() did not completed, see above')
        sys.exit()


if run_command_line==False: 
    err=False
    #running get_effective_angles() for SZA and OZA
    try:
        SZA_eff, slope, aspect, slope_flag=get_effective_angles('SZA')
    except:
        print('ERROR: get_effective_angles() did not completed, see above')
        err=True
        
    if err==False:
        try:
            OZA_eff=get_effective_angles('OZA')
        except:
            print('ERROR: get_effective_angles() did not completed, see above')

    
    if err==False:
        #running get_IBOAR for IBOAR at a given band
        try:
            get_IBOAR(slope,aspect,slope_flag)
        except:
            print('ERROR: get_IBOAR() did not completed, see above')    
            
if time_it==True:
    end_time = time.time()
    processing_time=(end_time - start_time)/60
    print('--- Processing time: %.3f minutes ---' %processing_time)
