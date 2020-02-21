# -*- coding: utf-8 -*-
"""
Created on Wed Feb 19 16:12:07 2020

@author: Adrien Wehrlé, GEUS (Geological Survey of Denmark and Greenland)

Compute the correlation (linear regression) between two variables stored in 
rasters over a given specific area. 
The default variables are the Snow Grain Diameter (SGD) and the percentage 
of variations between the Bottom Of Atmosphere Reflectance (BOAR) and the 
Intrinsic Bottom Of Atmosphere Reflectance (IBOAR). 
The function is run by multiprocessing to drastically decrease computation 
time.
This example can be easily modified with other variables and function to 
apply.

INPUTS:
    SGD, B: variables to analyse [string]
    outpath: path to the folder to store the output [string]
    output_name: name of the output that will be stored in a .tif file [string]
    resolution: side length of the specific area in pixels. [int]
                     
    
OUTPUTS:
    {outpath}{output_name}.tif: outputs stored in a .tif file. It has the same 
                                metadata as the inputs [.tif]
    if the variables have different dimensions:
        {var}_resampled.tif: Downsampling of the variable with the highest 
                             resolution [.tif]
        
    
"""


import numpy as np
import rasterio
import scipy
from scipy import stats
#from tqdm import tqdm
import multiprocessing
from multiprocessing import Pool
import time
from osgeo import gdal, gdalconst

SGD='/srv/home/8675309/AW/B_corr/albedo_bb_planar_sw.tif'
B='/srv/home/8675309/AW/B_corr/diff_iobar_boar.tif'
outpath='/srv/home/8675309/AW/B_corr/'
output_name='correlations_bba'



class SGD_B_correlation():
    
    def __init__(self, SGD=SGD, B=B, resolution=4):
        self.res=resolution/2
        self.SGD=SGD
        self.B=B
        

    def get_variables_names(self):
        v1=self.SGD
        v2=self.B
        return v1,v2
    
    def load_variables(self):
        rSGD=rasterio.open(self.SGD).read(1)
        rB=rasterio.open(self.B).read(1)
        return rSGD,rB
    
    def variables_dimensions(self):
        SGD_dims=np.shape(SGD)
        B_dims=np.shape(B)
        return SGD_dims, B_dims
        
    
    def get_combinations(self):
        mesh = np.array(np.meshgrid(np.arange(0,B.shape[0]),np.arange(0,B.shape[1])))
        combinations = mesh.T.reshape(-1, 2)
        
        return combinations
    
    def correlation(self,k):
        if k%1E8==0:
            print(k,'/',len(combinations))
        posx=combinations[k][0]
        posy=combinations[k][1]
        
        clipped_SGD=SGD[posx-self.res:posx+self.res,posy-self.res:posy+self.res]
        clipped_B=B[posx-self.res:posx+self.res,posy-self.res:posy+self.res]
        
        if np.sum(clipped_SGD)==0 or np.sum(clipped_B)==0:
            rvalue=np.nan
        else:
            results=scipy.stats.linregress(clipped_SGD.flatten(),clipped_B.flatten())
            rvalue=results.rvalue
        
        return rvalue
    
   
c=SGD_B_correlation()
SGD, B=c.load_variables()
SGD_dims, B_dims=c.variables_dimensions()
SGD_path, B_path=c.get_variables_names()


if SGD_dims!=B_dims:
    print('The variables have different dimensions... Downsampling the highest resolution...')
    variables = {np.prod(SGD_dims):SGD_path, np.prod(B_dims):B_path}
    
    #source
    src_filename = variables.get(max(variables))
    src = gdal.Open(src_filename, gdalconst.GA_ReadOnly)
    src_proj = src.GetProjection()
    src_geotrans = src.GetGeoTransform()
    
    #raster to match
    match_filename = variables.get(min(variables))
    match_ds = gdal.Open(match_filename, gdalconst.GA_ReadOnly)
    match_proj = match_ds.GetProjection()
    match_geotrans = match_ds.GetGeoTransform()
    wide = match_ds.RasterXSize
    high = match_ds.RasterYSize
    
    #output/destination
    to_resample_name=variables.get(max(variables)).split('/')[-1].split('.')[0]
    dst_filename = outpath+to_resample_name+'_resampled.tif'
    dst = gdal.GetDriverByName('Gtiff').Create(dst_filename, wide, high, 1, gdalconst.GDT_Float32)
    dst.SetGeoTransform( match_geotrans )
    dst.SetProjection( match_proj)
    
    #run
    gdal.ReprojectImage(src, dst, src_proj, match_proj, gdalconst.GRA_NearestNeighbour)
    del dst # Flush
    
    c.__init__(SGD=variables.get(min(variables)), B=dst_filename)
    SGD, B=c.load_variables()
    
    

B[np.isnan(SGD)]=np.nan
combinations=c.get_combinations()



nb_cores=multiprocessing.cpu_count()
start_time = time.time()
   
if __name__ == '__main__':
    rvalues=np.zeros((SGD.shape[0],SGD.shape[1]))
    op=0
    
    with Pool(nb_cores) as p:
        for rv in p.map(c.correlation, range(0,len(combinations))):
            x=combinations[op][0]
            y=combinations[op][1]
            rvalues[x,y]=rv
            op=op+1
            
end_time = time.time()
duration=(end_time - start_time)/60
print("--- Processing time: %.5f minutes ---" %duration)
   



temp=rasterio.open(SGD_path)
profile=temp.profile
profile.update(dtype=rasterio.float64)

with rasterio.open(outpath+output_name+'.tif', 'w', **profile) as dst:
        dst.write(rvalues, 1)
