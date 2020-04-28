# -*- coding: utf-8 -*-
"""

@author: Adrien Wehrlé, GEUS (Geological Survey of Denmark and Greenland)

Clip, reproject and compress ESA Land Classes (ESALC) for a given region. Convert the 
resulting .tif file to be used as a SICE mask.

Iceland, Svalbard, FransJosefLand, NovayaZemlya, SevernayaZemlya, JanMayen, 
NorthernArcticCanada, SouthernArcticCanada, Norway, Beaufort and AntarcticPeninsula 
are currently implemented.

Function is run in default mode at the end of the script.

WARNING: all the variables temporary stored in memory will be cleared to enable 
the deletion of temporary outputs. 

"""




def extract_esalc(esa_lc='/srv/home/8675309/AW/C3S-LC-L4-LCCS-Map-300m-P1Y-2018-v2.1.data/lccs_class.img',
                  source_crs='EPSG:4326',
                  region='Iceland',
                  outpath='/srv/home/8675309/AW/',
                  target_crs='EPSG:3413',
                  clean_temp_files=True,
                  to_SICEMask=True,
                  binary_mask=False,
                  verbose=True):
    '''
    INPUTS:
        esa_lc: path of ESA Land Classes .img file [string]
        source_crs: CRS of ESA Land Classes, default to 4326 [string]
        region: region to clip [string]
        outpath: folder where to store outputs [string]
        target_crs: Output CRS [string]
        to_SICEMask: set to True to have a SICE useable mask as output [boolean]
        binary_mask: set to True to have a SICE useable binary mask (land/ocean) 
                     if False, mask contains the 22 ESALC [boolean]
        verbose: set to True to print details about processing [boolean]
    
    OUTPUTS:
        if to_SICEMASK set to True:
            {outpath}/{region}.tif: binary or ESALC (depending on
                                    binary_mask option) SICE useable mask  for 
                                    the selected region [.tif]
        if to_SICEMASK set to False:
            {outpath}/esalc__clipped_{region}.tif: clipped ESALC for the selected 
                                               region [.tif]
            {outpath}/esalc_clipped_{region}_{target_crs}.tif: clipped and reprojected
                                                               in {target_crs}
                                                               ESALC for the selected 
                                                               region [.tif]
        
    
    
    '''
    
    
    import rasterio
    from shapely.geometry import box
    import geopandas as gpd
    from fiona.crs import from_epsg
    from rasterio.mask import mask
    from rasterio.warp import calculate_default_transform, reproject, Resampling
    import os
    from IPython import get_ipython
    
    
    #clear all variables to enable file deletion
    get_ipython().magic('reset -sf') 
        
    #initialize output names
    target_crs_name=target_crs.split(':')[1]
    out_tif=outpath+'esalc_clipped_'+region+'.tif'
    out_tif_3413=outpath+'esalc_clipped_'+target_crs_name+'_'+region+'.tif'
    SICEmask_tif=outpath+region+'.tif'
    
    #Delete outputs if already exists
    if os.path.exists(out_tif):
        if verbose:
          print('WARNING: Clipped ESA LC already exists...')
          print('Deleting clipped ESA LC...')
        os.remove(out_tif)
    if os.path.exists(out_tif_3413):
        if verbose:
          print('WARNING: Reprojected and clipped ESA LC already exists...')
          print('Deleting reprojected and clipped ESA LC...')
        os.remove(out_tif_3413)
    if os.path.exists(SICEmask_tif):
        if verbose:
          print('WARNING: SICE mask already exists...')
          print('Deleting SICE mask...')
    
    
    
    data = rasterio.open(esa_lc)
    
    
    if source_crs=='EPSG:4326':
        
        if region=='Greenland':
            minx, miny =  -80.35, 56.33
            maxx, maxy = -3.17, 84.17
            bbox = box(minx, miny, maxx, maxy)
            
        elif region=='Iceland':
            minx, miny = -24.93, 63.18
            maxx, maxy = -12.8, 66.6
            bbox = box(minx, miny, maxx, maxy)
        
        elif region=='Svalbard':
            minx, miny = 7.65, 76.18
            maxx, maxy = 37.3, 80.84
            bbox = box(minx, miny, maxx, maxy)
            
        elif region=='NovayaZemlya':
            minx, miny = 47.64, 70.4
            maxx, maxy = 70.96, 77.22
            bbox = box(minx, miny, maxx, maxy)
        
        elif region=='FransJosefLand':
            minx, miny = 40.88, 79.85
            maxx, maxy = 71.66, 81.93
            bbox = box(minx, miny, maxx, maxy)
        
        elif region=='SevernayaZemlya':
            minx, miny = 82.77, 78.00
            maxx, maxy = 112.26, 83.11
            bbox = box(minx, miny, maxx, maxy)
        
        elif region=='JanMayen':
            minx, miny = -9.47, 70.77
            maxx, maxy = -7.45, 71.21
            bbox = box(minx, miny, maxx, maxy)
        
        elif region=='NorthernArcticCanada':
            minx, miny = -128.27, 73.78
            maxx, maxy = -57.69, 83.24
            bbox = box(minx, miny, maxx, maxy)
            
        elif region=='SouthernArcticCanada':
            minx, miny = -92.23, 61.19
            maxx, maxy = -60.96, 74.43
            bbox = box(minx, miny, maxx, maxy)
        
        elif region=='Norway':
            minx, miny = 4.49, 59.44
            maxx, maxy = 9.08, 62.12
            bbox = box(minx, miny, maxx, maxy)
            
        elif region=='Beaufort':
            minx, miny = -148.87, 68.28
            maxx, maxy = -122.28, 75.39
            bbox = box(minx, miny, maxx, maxy) 
            
        elif region=='AntarcticPeninsula':
            minx, miny = -78.23, -74.76
            maxx, maxy = -49.23, -57.98
            bbox = box(minx, miny, maxx, maxy)
            
        elif region=='AlaskaYukon':
            minx, miny = -158.07, 54.96
            maxx, maxy = -127.22, 64.42
            bbox = box(minx, miny, maxx, maxy)
            
        else:
            if verbose:
              print('Wrong region name or not implemented')
            return
            
            
    elif source_crs=='EPSG:3413':
        
        if region=='Iceland':
                minx, miny = 825968.82, -2422134.15
                maxx, maxy = 1405420.90, -2377180.81
                bbox = box(minx, miny, maxx, maxy)
            
        elif region=='Svalbard':
            minx, miny = 7.65, 76.18
            maxx, maxy = 37.3, 80.84
            bbox = box(minx, miny, maxx, maxy)
                
        elif region=='Novaya Zemlya':
            minx, miny = 47.64, 70.4
            maxx, maxy = 70.96, 77.22
            bbox = box(minx, miny, maxx, maxy)
        
        else:
            if verbose:
              print('Wrong region name or not implemented')
            return
            
        
    
    
    #insert the bbox into a GeoDataFrame
    geo = gpd.GeoDataFrame({'geometry': bbox}, index=[0], crs=from_epsg(4326))
    
    #reproject to the raster crs (safer)
    geo = geo.to_crs(crs=data.crs.data)
    
    #coordinates of the geometry so that rasterio handles it
    def getFeatures(gdf):
        """Function to parse features from GeoDataFrame in such a manner that rasterio wants them"""
        import json
        return [json.loads(gdf.to_json())['features'][0]['geometry']]
    
    if verbose:
      print('Creating mask...')
    coords = getFeatures(geo)
    
    #clip source image using coords
    if verbose:
      print('Clipping input...')
    out_img, out_transform = mask(dataset=data, shapes=coords, crop=True)
    
    # Copy the metadata
    out_meta = data.meta.copy()
    
    out_meta.update({"driver": "GTiff",
                    "height": out_img.shape[1],
                    "width": out_img.shape[2],
                    "transform": out_transform,
                    "crs": data.crs})
    
    if verbose:
      print('Saving output...')
    with rasterio.open(out_tif, "w",compress='deflate', **out_meta) as dest:
        dest.write(out_img)
        

    if source_crs != target_crs:
        if verbose:
          print('Reprojecting output...')
        dst_crs = target_crs
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
    
    
    if to_SICEMask:
        '''
        ESA LC:
            210: ocean
            0: out of footprint
            60-90(10)/100-150(10)/122/180/200-220(10): land 
        
        SICE MASK:
            255: ocean
            2: land
        '''
        
        print('Converting output to SICE mask...')
        esalc_tp=rasterio.open(out_tif_3413)
        esalc=esalc_tp.read(1)
        
        if binary_mask:
            if region!='BeaufortSea':
                mask_esalc=esalc.copy()
                mask_esalc[(mask_esalc!=210) & (mask_esalc!=0)]=2
                mask_esalc[mask_esalc!=2]=255
            else:
                mask_esalc=esalc.copy()
                mask_esalc[(mask_esalc==210) & (mask_esalc!=0)]=2
                mask_esalc[mask_esalc!=2]=255
            
        elif not binary_mask:
            if region!='BeaufortSea':
                mask_esalc=esalc.copy()
                mask_esalc[mask_esalc==210]=255
                mask_esalc[mask_esalc==0]=255
            else:
                if verbose:
                  print('BeaufortSea mask could only be binary (covers ocean only)')
                mask_esalc=esalc.copy()
                mask_esalc[(mask_esalc==210) & (mask_esalc!=0)]=2
                mask_esalc[mask_esalc!=2]=255
        
        if verbose:
          print('Saving SICE mask...')
        profile = esalc_tp.profile 
        profile.update(nodata=255) 
        
        with rasterio.open(SICEmask_tif, 'w', **profile) as dst:
            dst.write(mask_esalc, 1)
            
        
        return out_tif, out_tif_3413, clean_temp_files,to_SICEMask
        
        
verbose=True

out_tif, out_tif_3413, clean_temp_files,to_SICEMASK=extract_esalc()

#turn temporary outputs to final if SICEMask isn't needed
if not to_SICEMASK:
    clean_temp_files=False
    
if clean_temp_files:
    if verbose:
      print('Deleting temporary outputs...')
    import os
    os.remove(out_tif)
    os.remove(out_tif_3413)
