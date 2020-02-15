# -*- coding: utf-8 -*-
"""
This script read USGS streamflow data.

Created on Fri Feb 14 00:21:31 2020

@author: Michael Ou

usage:
    python swat_plot.py 
"""



import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from urllib.request import urlopen

#%% read usgs gauge data
class usgs_data_reader:
    def read_usgs_rdb(filepath_or_link):      
        return pd.read_csv(filepath_or_link, comment='#', header=0, sep='\t')[1:].apply(lambda x: pd.to_numeric(x, errors='ignore') if x.name.endswith('_va') else x, axis=0)
       
    def create_daily_streamflow_url(gauge_list, begin_date='1900-01-01', end_date='2019-12-31'):
        import datetime
        try:
            bdate = datetime.date.fromisoformat(begin_date)
            edate = datetime.date.fromisoformat(end_date)
        except:
            raise ValueError ("The input formats for the begin_date and end_date must be YYYY-MM-DD")
            
        if type(gauge_list) is not list:
            raise TypeError('The gagelist must be a list type.')
        
        if gauge_list == []:
            raise ValueError('The gagelist must not be an empty list.')
            
        gages = ('&site_no={}' * len(gauge_list)).format(*gauge_list)
        period = f'&period=&begin_date={begin_date}&end_date={end_date}'
        return f'https://waterdata.usgs.gov/nwis/dv?&cb_00060=on&format=rdb{gages}&referred_module=sw{period}'
    
    def create_monthly_streamflow_url(gauge_list, begin_date='1900-01-01', end_date='2019-12-31'):
        try:
            bdate = datetime.date.fromisoformat(begin_date)
            edate = datetime.date.fromisoformat(end_date)
        except:
            raise ValueError ("The input formats for the begin_date and end_date must be YYYY-MM-DD")
            
        if type(gauge_list) is not list:
            raise TypeError('The gagelist must be a list type.')
        
        if gauge_list == []:
            raise ValueError('The gagelist must not be an empty list.')
        
        
        gages = ''.join(['&site_no={0}&por_{0}_93535=594467,00060,93535,{1:.7},{2:.7}'.format(g, begin_date, end_date)  for g in gauge_list])
    
        return f'https://waterdata.usgs.gov/nwis/monthly?referred_module=sw&format=rdb{gages}'



