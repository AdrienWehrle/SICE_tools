# -*- coding: utf-8 -*-
"""
Created on Mon Feb 10 09:49:10 2020

@author: Adrien Wehrlé, GEUS (Geological Survey of Denmark and Greenland)

Clip ArcticDEM derived slopes for a given region based on a mask. 
Slopes have been processed using SNAP slopes calculator.

Function is run in default mode at the end of the script.

WARNING: all the variables temporary stored in memory will be cleared to enable 
the deletion of temporary outputs. 

"""


def extract_arcticdem(adem_slope='H:/arcticdem_mosaic_500m_v3.0_slope.data/slope.img',
                       region='NovayaZemlya',
                       regional_mask='C:/Users/Pascal/Desktop/GEUS_2019/masks/github/NovayaZemlya.tif',
                       outpath='C:/Users/Pascal/Desktop/GEUS_2019/tempo/',
                       aspect=False):
    
    '''
    INPUTS:
        adem_slope: path of ArcticDEM .tif file [string]
        region: region to clip [string]
        regional_mask: path of the mask associated to the selected region [.tif]
        outpath: folder where to the clipped ArcticDEM [string]
        
    OUTPUTS:
        {outpath}/{region}_arcticdem_slope.tif: clipped ArcticDEM (EPSG: 3413) [.tif]
        {outpath}/{region}_mask_resampled.tif: resampled mask to fit clipped 
                                               ArcticDEM resolution [.tif]
    
    '''
    
    
    import rasterio
    from shapely.geometry import box
    import geopandas as gpd
    from rasterio.mask import mask
    from rasterio.warp import calculate_default_transform, reproject, Resampling
    from IPython import get_ipython
    import os
    from osgeo import gdal, gdalconst
    
    
    #clear all variables to enable file deletion
    get_ipython().magic('reset -sf') 
    
    if aspect==False:
        print('\n')
        print('Running extract_arctidem for %s... [SLOPE]' %region)
    if aspect==True:
        print('\n')
        print('ASPECT: Running extract_arctidem for %s... [ASPECT]' %region)
    
    #initialize output name
    target_crs='EPSG: 3413'
    target_crs_name=target_crs.split(':')[1]
        
    out_tif=outpath+region+'_adem_slope'+'.tif'
    out_tif_3413=outpath+region+'_arcticdem_slope_temp'+'.tif'
    
    #delete outputs if already exists
    if os.path.exists(out_tif)==True:
        if aspect==False:
            print('WARNING: Clipped ArcticDEM derived slopes already exist...')
            print('Deleting Clipped ArcticDEM derived slopes...')
        elif aspect==False:
            print('WARNING: Clipped ArcticDEM derived slope aspect already exist...')
            print('Deleting Clipped ArcticDEM derived slope aspect...')
        os.remove(out_tif)
        
    if os.path.exists(out_tif_3413)==True:
        if aspect==False:
            print('WARNING: Reprojected and clipped ArcticDEM derived slopes already exist...')
            print('Deleting reprojected and clipped ArcticDEM derived slopes...')
        elif aspect==True:
            print('WARNING: Reprojected and clipped ArcticDEM derived slope aspect already exist...')
            print('Deleting reprojected and clipped ArcticDEM derived slope aspect...')
        os.remove(out_tif_3413)
    
    data = rasterio.open(adem_slope)
    regional_mask_path=regional_mask
    regional_mask=rasterio.open(regional_mask)
    
    #create the bbox with regional_mask dimensions
    lower_right_corner=regional_mask.transform * (regional_mask.width, regional_mask.height)
    upper_left_corner=regional_mask.transform * (0, 0)
    bbox = box(upper_left_corner[0], lower_right_corner[1], lower_right_corner[0], upper_left_corner[1])
            
            
    
    #insert the bbox into a GeoDataFrame
    geo = gpd.GeoDataFrame({'geometry': bbox}, index=[0], crs=data.crs)
    
    
    #coordinates of the geometry so that rasterio handles it
    def getFeatures(gdf):
        """Function to parse features from GeoDataFrame in such a manner that rasterio wants them"""
        import json
        return [json.loads(gdf.to_json())['features'][0]['geometry']]
    
    print('Creating mask...')
    coords = getFeatures(geo)
    
    #clip source image using coords
    print('Clipping input...')
    out_img, out_transform = mask(dataset=data, shapes=coords, crop=True)
    
    #mask output image
    out_img[regional_mask==255]=0
    
    #copy the metadata
    out_meta = data.meta.copy()
    
    out_meta.update({"driver": "GTiff",
                    "height": out_img.shape[1],
                    "width": out_img.shape[2],
                    "transform": out_transform,
                    "crs": regional_mask.crs})
    
    print('Saving output...')
    with rasterio.open(out_tif, "w",compress='deflate', **out_meta) as dest:
        dest.write(out_img)
        

        
    print('Reprojecting output...')
    dst_crs = regional_mask.crs
    with rasterio.open(out_tif) as src:
        transform, width, height = calculate_default_transform(src.crs, dst_crs, 
                                                                src.width, 
                                                                src.height, 
                                                                *src.bounds)
        kwargs = src.meta.copy()
        kwargs.update({'crs': dst_crs,'transform': transform, 'width': width,'height': height})
    
        with rasterio.open(out_tif_3413, 'w', compress='deflate', **kwargs) as dst:
                reproject(source=rasterio.band(src, 1),destination=rasterio.band(dst, 1),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.nearest)
    

    print('Resampling mask to fit output resolution...')
    #source
    src_filename = regional_mask_path
    src = gdal.Open(src_filename, gdalconst.GA_ReadOnly)
    src_proj = src.GetProjection()
    src_geotrans = src.GetGeoTransform()
    
    #raster to match
    match_filename = out_tif_3413
    match_ds = gdal.Open(match_filename, gdalconst.GA_ReadOnly)
    match_proj = match_ds.GetProjection()
    match_geotrans = match_ds.GetGeoTransform()
    wide = match_ds.RasterXSize
    high = match_ds.RasterYSize
    
    #output/destination
    dst_filename = outpath+region+'mask_resampled_temp.tif'
    dst = gdal.GetDriverByName('Gtiff').Create(dst_filename, wide, high, 1, gdalconst.GDT_Float32)
    dst.SetGeoTransform( match_geotrans )
    dst.SetProjection( match_proj)
    
    #run
    gdal.ReprojectImage(src, dst, src_proj, match_proj, gdalconst.GRA_NearestNeighbour)
    
    del dst # Flush
    
    
    print('Masking output...')
    
    mask=rasterio.open(outpath+region+'mask_resampled_temp.tif')
    mask_data=mask.read(1)
    output=rasterio.open(out_tif_3413)
    output_data=output.read(1)
    profile_mask=mask.profile
    profile_output = output.profile #saving metadata
    output_data[mask.read(1)==0]=0
    mask_data[mask_data==0]=255
    profile_mask.update(nodata=255)
    
    if aspect==False:
        
        with rasterio.open(outpath+region+'_arcticdem_slope'+'.tif', 'w', **profile_output) as dst:
            dst.write(output_data, 1)
        with rasterio.open(outpath+region+'_mask_resampled.tif', 'w', **profile_output) as dst:
            dst.write(mask_data, 1)
            
    if aspect==True:
        with rasterio.open(outpath+region+'_arcticdem_aspect'+'.tif', 'w', **profile_output) as dst:
            dst.write(output_data, 1)
    

    
    temp=outpath+region+'mask_resampled_temp.tif'
    
    return out_tif,out_tif_3413,temp
    

import os

regions= ['Iceland', 'Svalbard', 'FransJosefLand', 'NovayaZemlya',
          'SevernayaZemlya', 'JanMayen', 'NorthernArcticCanada', 
          'SouthernArcticCanada']

inpath='C:/Users/Pascal/Desktop/GEUS_2019/masks/github/'

for reg in regions:
    
    region_path=inpath+reg+'.tif'
    out_tif,out_tif_3413,temp=extract_arcticdem(regional_mask=region_path,region=reg,aspect=False)
    print('Deleting temporary outputs...')
    os.remove(out_tif)
    os.remove(out_tif_3413)
    os.remove(temp)
    out_tif,out_tif_3413,temp=extract_arcticdem(adem_slope='H:/arcticdem_mosaic_500m_v3.0_slope.data/aspect.img',
                                                regional_mask=region_path,
                                                region=reg,aspect=True)
    print('Deleting temporary outputs...')
    os.remove(out_tif)
    os.remove(out_tif_3413)
    os.remove(temp)
    
    for i in range(4):
        print('\n')





        
        



    
