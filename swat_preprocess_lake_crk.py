# -*- coding: utf-8 -*-
"""


@author: Michael Ou

This script is first developed by Gengxin (Michael) Ou on 2/18/2015 in R
https://gist.github.com/ougx/cb33a1cf761dea01fa0d#file-swat_preprocess-r

It was converted to Python on Sat Feb 15 18:54:54 2020

usage:
    python script.py ars_data.zip hint_wspd.zip

Study area:
    West  -98.590528    East  -98.439062 
    North  35.469812    South  35.285992 

"""

import os
import zipfile
import pandas as pd
import sys
import numpy as np
import datetime
#%% some parameters
ars_stations = [102, 106, 107, 110, 112]    
start_date = np.datetime64('2005-08-01')
end_date   = np.datetime64('2009-02-28')

ars_weather_var = {'pcp':('RAINt', 1.0), 'rh':('RELHa', 0.01), 'tmp':(['TAIRx', 'TAIRn'], 1.0), 'srad':('SRADt', 1.0)}

output_dir = 'WeatherData'
#%%
##################################### ARS Micronet #################################### 

#read and combine the ars data
# STID - station ID -- required
# DM - day of the month (CST) -- required
# RAINt - total rainfall (mm); See Notes
# SRADt - total solar radiation (MJ/m^2)
# RELH(a/x/n) - (ave/max/min) relative humidity at 1.5 m (%)
# TAIR(a/x/n) - (ave/max/min) air temperature at 1.5 m (deg C)
# TS05(a/x/n) - (ave/max/min) soil temperature at 05 cm depth (deg C)
# TS10(a/x/n) - (ave/max/min) soil temperature at 10 cm depth (deg C)
# TS15(a/x/n) - (ave/max/min) soil temperature at 15 cm depth (deg C)
# TS25(a/x/n) - (ave/max/min) soil temperature at 25 cm depth (deg C)
# TS30(a/x/n) - (ave/max/min) soil temperature at 30 cm depth (deg C)
# TS45(a/x/n) - (ave/max/min) soil temperature at 45 cm depth (deg C)
# VW05(a/x/n) - (ave/max/min) volumetric water content at 5 cm depth (water fraction by volume)
# VW25(a/x/n) - (ave/max/min) volumetric water content at 25 cm depth (water fraction by volume)
# VW45(a/x/n) - (ave/max/min) volumetric water content at 45 cm depth (water fraction by volume)
# SKIN(a/x/n) - (ave/max/min) skin temperature (deg C) [available at a select number of Little Washita sites only]

# g - good (passed QC tests - extremely low probability of error)
# S - suspect (QC tests indicate some suspicion - low probability of error)
# W - warning (several QC test failures - high probability of error)
# F - failure (known error)
# M - missing (data not received)
# I - ignore
# N - not installed
# U - unknown

assert len(sys.argv) > 2, 'Specify the ARS data file and wind speed file\n{}'.format(sys.argv)
    



ars_zip = sys.argv[1]
wspd_zip = sys.argv[2]

assert os.path.exists(ars_zip),  'The ARS weather data file "{}" does not exist.'.format(ars_zip)
assert os.path.exists(wspd_zip), 'The wind speed data file "{}" does not exist.'.format(wspd_zip)

if not os.path.exists(output_dir):
    os.mkdir(output_dir)


df_weather = pd.DataFrame(np.nan, columns=['RAINt', 'SRADt', 'RELHa', 'TAIRn', 'TAIRx'], index=pd.date_range(start_date, end_date, freq='D'))
with zipfile.ZipFile(ars_zip, 'r') as datazip:
    months = pd.date_range(start_date, end_date, freq='MS')
    for s in ars_stations:
        weather_vars = ['RAINt', 'SRADt', ]
        for m in months:
            with datazip.open('{:%Y%m}f{}.txt'.format(m, s)) as f:
                df = pd.read_csv(f, skiprows=4, header=0, sep=' ', skipinitialspace =True)
                df.index = pd.date_range(m, periods=m.days_in_month, freq='D')
                df_weather.loc[df.index,:] = df 
        
        df_weather = df_weather.where(df_weather>-900).fillna(method='pad')   
        for k, v in ars_weather_var.items():
            val = (df_weather[v[0]] * v[1])
            csv = os.path.join(output_dir, '{}{}.txt'.format(k, s))
            with open(csv,'w') as fo:
                fo.write('{:%Y%m%d}\n'.format(pd.to_datetime(start_date)))
                val.to_csv(fo, header=False, index=False)


# Precipitation Gage Location Table
# ID Integer Gage identification number (not used by interface)
# NAME String max 8 chars Corresponding table name string
# LAT Floating point Latitude in decimal degrees
# LONG Floating point Longitude in decimal degrees
# ELEVATION integer Elevation of rain gage (m)

# Temperature Gage Location Table (ASCII Only)
# ID Integer Gage identification number (not used by interface)
# NAME String max 8 chars Corresponding table name string
# LAT Floating point Latitude in decimal degrees
# LONG Floating point Longitude in decimal degrees
# ELEVATION integer Elevation of temperature gage (m)

# solar/wind/relative humidity gage
# ID Integer Gage identification number (not used by interface)
# NAME String max 8 chars Corresponding table name string
# LAT Floating point Latitude in decimal degrees
# LONG Floating point Longitude in decimal degrees
# ELEVATION integer Elevation of solar/wind/RH gage (m)
                
ars_list = pd.read_csv('http://ars.mesonet.org/sites/default/files/2017-12/geoars_0.csv', skiprows=41, header=None)
ars_list_columns = {'NAME':1, 'LAT':7, 'LONG':8, 'ELEVATION':9}

    
ars_list.index = ars_list[ars_list_columns['NAME']].apply(lambda x: int(x[-3:]))
ars_list.index.name = 'ID'
colnames = ars_list.columns.tolist()
for i in ars_list_columns:
    colnames[ars_list_columns[i]] = i
ars_list.columns = colnames
for k in ars_weather_var:
    ars_list['NAME'] = ars_list['NAME'].apply(lambda x: k+x[-3:])
    ars_list.loc[ars_stations, ['NAME', 'LAT', 'LONG', 'ELEVATION']].to_csv(os.path.join(output_dir, 'list_{}.txt'.format(k)))

#%% wind speed
filename = os.path.basename(wspd_zip).strip().split('.')[0] 
with zipfile.ZipFile(wspd_zip, 'r') as datazip:
    with datazip.open('{}.csv'.format(filename)) as f:
        df_wspd = pd.read_csv(f)
df_wspd.index = df_wspd.apply(lambda x: datetime.datetime(x['YEAR'], x['MONTH'], x['DAY']), axis=1)
df_wspd = df_wspd[start_date: end_date]
# speed is in mph
df_wspd.WSPD = (df_wspd.WSPD.where(df_wspd.WSPD>-900) * 0.4470389).fillna(-99.)

with open(os.path.join(output_dir, 'wspd.txt'),'w') as fo:
    fo.write('{:%Y%m%d}\n'.format(pd.to_datetime(start_date)))
    df_wspd.WSPD.to_csv(fo, header=False, index=False)

# write wind speed list table
with open(os.path.join(output_dir, 'list_wspd.txt'),'w') as fo:
    fo.write('ID,NAME,LAT,LONG,ELEVATION\n')
    fo.write('1,wspd,35.48439,-98.48151,493\n')

##################################### USGS Streamflow ####################################
#processing streamflow data
obsites = ("07325840","07325850")



print('\n\nPreprocesssing completed sucesuffuly')