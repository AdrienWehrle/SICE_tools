# -*- coding: utf-8 -*-
"""

@author: Adrien Wehrlé, Jason E. Box, GEUS (Geological Survey of Denmark and Greenland), SICE project

Check the availability of SICE products.
At the end of the script, the user can set the option multi_proc to True if the processing 
is too long. It allows to run the function by multiprocessing using the nb_cores (given by 
the user) and drastically decrease computation time. 

"""

def data_availability_check(inpath='/srv/home/8675309/SICEv0/',
                            outpath='/srv/home/8675309/data_availability/',
                            variables='/srv/home/8675309/data_availability/SICE_products.csv',
                            variables_date=None,
                            variables_extension='.tif',
                            visualisation=False,
                            fig_save=True,
                            fig_path='/srv/home/8675309/data_availability/',
                            fig_extension='eps'):
    
    '''
    INPUTS:
        inpath: path to targeted dataset [string]
        outpath: path to result csv file [string]
        variables: variables to check [list] or path to csv 
                   file containing variables in product_file_name 
                   column (default) [.csv]
        variables_date: if variables are unkown, pass a date (YYYYMMDD) where 
                        the variables to check are available. Otherwise, set to 
                        None (default) [string,NoneType]
        variables_extension: extension of the files in which variables to check 
                             are stored [string]
        visualisation: visualisation created if True (False as default) [bool]
        fig_save: figure named data_avail.[fig_extension] saved if True (True as default) [bool]
        fig_path: Path where to save the figure [string]
        fig_extension: Extension with which the figure is saved (eps as default) [string]
        
    OUTPUTS:
        data_availability: matrix with dates in rows and variables in columns [dataframe]
        data_availability_from_{start_date}_to{end_date}.csv: file containing data_availability,
                                                              stored in outpath [.csv]
    
    '''
    
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import glob
    import os
    from tqdm import tqdm #progress bar
    
    #set default plot parameters (ESA font)
    plt.rcParams['font.sans-serif'] = ['Georgia']
    plt.rcParams["font.size"] = 12

    #look for variables from a given file if unknown
    if type(variables_date)==str:
        variables_filenames=list(np.sort(glob.glob(inpath+variables_date+os.sep+'*'+variables_extension)))
        variables=[i.split(os.sep)[-1].split('.')[0] for i in variables_filenames]
        
        if variables_date in variables: #dealing with tifs that are not variables
            variables.remove(variables_date)    
            
    if '.csv' in variables: #if csv containing variables is given
        variables_csv=pd.read_csv(variables)
        variables=variables_csv['product_file_name']
        
    files_names=list(np.sort(glob.glob(inpath+'2019*'))) #list all files needed 
    files_names=[os.path.normpath(f) for f in files_names] #generalize paths

    
    #start and end dates as datetimes 
    start_date=pd.to_datetime(files_names[0].split(os.sep)[-1],format='%Y%m%d')
    end_date=pd.to_datetime(files_names[-1].split(os.sep)[-1],format='%Y%m%d')

    nb_days=(end_date-start_date).days+1 #duration
    date_list=pd.date_range(start = start_date, periods = nb_days) #list of expected dates
    data_availability=pd.DataFrame(columns = variables) 
    data_availability['date']=date_list #filling rows with expected dates
    data_availability.loc[:, data_availability.columns != 'date']=0 #filling variables with 0
    
    #data availability updated only if date and variable exists
    for j,file in tqdm(enumerate(files_names)): 
        #date check
        if np.sum(pd.to_datetime(file.split(os.sep)[-1],format='%Y%m%d')==data_availability['date'])==1:
            available_variable_filenames=list(np.sort(glob.glob(inpath+str(file.split(os.sep)[-1])
                                           +os.sep+'*'+variables_extension)))
                
            for var in variables:
                #variables check
                if len([s for s in available_variable_filenames if var in s])>=1:
                    indx=np.where(pd.to_datetime(file.split(os.sep)[-1],format='%Y%m%d')==data_availability['date'])[0]
                    data_availability.at[indx,var]=1
        
        elif np.sum(pd.to_datetime(file.split(os.sep)[-1],format='%Y%m%d')==data_availability['date'])>1:
            print('!!! WARNING: FILE DUPLICATES !!!')
                    
            
    dates_str = [d.strftime('%Y-%m-%d') for d in data_availability['date']]   
    output_filename=outpath+'data_availability_from_'+dates_str[0]+'_to_'+dates_str[-1]+'.csv'
    data_availability.to_csv(output_filename,index=False)         
    
    if visualisation:
        vis_step=10 #plot yticks every vis_step tick
        for i in range(0,len(dates_str)):
            if i%vis_step==0:
                dates_str[i]=''
        fig, ax = plt.subplots()
        ax.imshow(data_availability.loc[:, data_availability.columns != 'date'],cmap='bwr_r',aspect='auto')
        ax.set_ylim(-0.5,data_availability.shape[0]-0.5)
        ax.set_xticks(np.arange(0,len(variables)))
        minor_ticksx = np.arange(0,len(variables))+0.5
        minor_ticksy = np.arange(0,data_availability.shape[0])+0.5
        ax.set_xticks(minor_ticksx, minor=True)
        ax.set_yticks(minor_ticksy, minor=True)
        ax.set_xticklabels(variables)
        ax.set_yticks(np.arange(0,data_availability.shape[0]))
        ax.set_yticklabels(dates_str)
        plt.xticks(rotation=80)
        ax.grid(which='minor',color='k', linewidth=2)
        plt.axhline(-0.5,color='black',linewidth=2)
        plt.axvline(-0.5,color='black',linewidth=2)
        plt.title('Data availability from %s to %s' %(dates_str[0],dates_str[-1]),fontsize=20)
        

        if fig_save:
            if fig_extension=='png':
                plt.savefig(fig_path+'data_avail.png', bbox_inches='tight',dpi=300)
            elif fig_extension=='eps':
                plt.savefig(fig_path+'data_avail.eps', bbox_inches='tight', format='eps')
            else:
                print('%s figure extension: not implemented' %fig_extension)
    
    return data_availability





'''
The section below is similar to data_availability_check(), just reformulated to 
correctly run by multiprocessing.
'''



multi_proc=False
visualisation=False
nb_cores=8

if multi_proc:
    
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import glob
    import time
    from multiprocessing import Pool
    
    inpath='C:\\Users\Adrien\\Dropbox\\AW\\Greenland\\'
    outpath='C:\\Users\Adrien\\Desktop\\GEUS_2019\\'
    variables=['OAA','OZA','Oa01_reflectance','Oa02_reflectance','Oa03_reflectance','Oa04_reflectance','Oa05_reflectance']
    variables_date='20190801'
    variables_extension='.tif'
    visualisation=False
    
    #look for variables from a given file if unknown
    if type(variables_date)==str:
        variables_filenames=list(np.sort(glob.glob(inpath+variables_date+'\\*'+variables_extension)))
        variables=[i.split('\\')[-1].split('.')[0] for i in variables_filenames]
        
        if variables_date in variables: #dealing with tifs that are not variables
            variables.remove(variables_date)    
        
    files_names=list(np.sort(glob.glob(inpath+'2019*'))) #list all files needed 
    
    #start and end dates as datetimes 
    start_date=pd.to_datetime(files_names[0].split('\\')[-1],format='%Y%m%d')
    end_date=pd.to_datetime(files_names[-1].split('\\')[-1],format='%Y%m%d')

    nb_days=(end_date-start_date).days+1 #duration
    date_list=pd.date_range(start = start_date, periods = nb_days) #list of expected dates
    
    def DAC_processing(file):
        
        data_availability_file=[]
        file_datetime=pd.to_datetime(file.split('\\')[-1],format='%Y%m%d')
        
        #date check
        if np.sum(file_datetime==data_availability['date'])==1:
            available_variable_filenames=list(np.sort(glob.glob(inpath+str(file.split('\\')[-1])
                                           +'\\*'+variables_extension)))
                
            for var in variables:
                #variables check
                if len([s for s in available_variable_filenames if var in s])>=1:
                    data_availability_file.append(1)
                else:
                    data_availability_file.append(0)
                    
        elif np.sum(pd.to_datetime(file.split('\\')[-1],format='%Y%m%d')==data_availability['date'])==0:
            data_availability_file=[0]*len(variables)
        
        elif np.sum(pd.to_datetime(file.split('\\')[-1],format='%Y%m%d')==data_availability['date'])>1:
            print('!!! WARNING: FILE DUPLICATES !!!')
    
        return data_availability_file,file_datetime
        
    
    #multiprocessing run    
    start_time = time.time()
    local_time = time.ctime(start_time)
    if __name__ == '__main__':
        data_availability_files=[]
        file_datetimes=[]
        with Pool(nb_cores) as p:
            for d_av,f_dt in p.map(DAC_processing, files_names):
                data_availability_files.append(d_av)
                file_datetimes.append(f_dt)
        
    print("--- %s seconds ---" % (time.time() - start_time))
    
    #creating the same output as data_availability_check() with multiprocessing results
    data_availability=pd.DataFrame(columns = variables) 
    data_availability['date']=date_list #filling rows with expected dates
    data_availability.loc[:, data_availability.columns != 'date']=0 #filling variables with 0
    data_availability.index=data_availability['date']
    
    for i,fs_dt in enumerate(file_datetimes): #filling data_availability with multiprocessing results
        data_availability[fs_dt]=data_availability_files[i]
        
    data_availability=data_availability.reset_index(drop=True)
    
    dates_str = [d.strftime('%Y-%m-%d') for d in data_availability['date']]
    output_filename=outpath+'data_availability_from_'+dates_str[0]+'_to_'+dates_str[-1]+'.csv'
    data_availability.to_csv(output_filename,index=False)   

    
    if visualisation:
        fig, ax = plt.subplots()
        ax.imshow(data_availability.loc[:, data_availability.columns != 'date'],cmap='bwr_r',aspect='auto')
        ax.set_xticks(np.arange(0,len(variables)))
        minor_ticksx = np.arange(0,len(variables))+0.5
        minor_ticksy = np.arange(0,data_availability.shape[0])+0.5
        ax.set_xticks(minor_ticksx, minor=True)
        ax.set_yticks(minor_ticksy, minor=True)
        ax.set_xticklabels(variables)
        ax.set_yticks(np.arange(0,data_availability.shape[0]))
        ax.set_yticklabels(dates_str)
        plt.xticks(rotation=80)
        ax.grid(which='minor',color='k', linewidth=2)
        plt.title('Data availability from %s to %s' %(dates_str[0],dates_str[-1]),fontsize=20)
